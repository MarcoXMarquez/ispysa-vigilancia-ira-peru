"""Validación con archivos temporales: las fallas no deben producir cifras ficticias."""

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

import numpy as np
import pandas as pd

from src.quality_panel import evidence_report, export_with_evidence
from src.services.data_service import EpidemiologyDataService
from src.services.model_service import EpidemiologyModelService


class TestDataQuality(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.annual_path = self.root / 'data/processed/annual_disease_measures_dept_2000_2023.csv'
        self.model_dir = self.root / 'outputs/national_children_cases_ml'
        self.annual = pd.DataFrame({
            'department': [f'DEPARTAMENTO {number}' for number in range(1, 26)],
            'iddpto': range(1, 26), 'year': 2023, 'population': 100000,
        })
        for group in ('men5', '60mas'):
            for kind, value in [('cases', 10), ('hosp', 2), ('death', 1)]:
                self.annual[f'{kind}_{group}'] = value
                self.annual[f'{kind}_rate_{group}'] = value
        self.metrics = pd.DataFrame({'model': ['xgboost'], 'mae': [0.1], 'rmse': [0.2], 'r2': [0.9]})
        self.forecasts = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=52, freq='7D').astype(str),
            'model': 'xgboost', 'predicted': 2.0,
        })

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(path, index=False)

    def model_path(self, suffix):
        return self.model_dir / f'national_children_cases_ml_{suffix}.csv'

    def test_valid_annual_data_has_correct_ratios_and_hash(self):
        self.write(self.annual_path, self.annual)
        service = EpidemiologyDataService(self.root)
        national = service.get_national_summary()
        self.assertEqual(national.iloc[0]['hr_men5'], 20)
        self.assertEqual(national.iloc[0]['cfr_men5'], 10)
        department = service.get_department_data('DEPARTAMENTO 1')
        self.assertEqual(department.iloc[0]['cfr_men5'], 10)
        evidence = next(iter(service.reader.evidence.values()))
        self.assertEqual(evidence['sha256'], sha256(self.annual_path.read_bytes()).hexdigest())
        self.assertEqual(evidence['estado'], 'Verificado')
        self.assertIsNone(evidence['generado_utc'])

    def test_invalid_annual_inputs_are_blocked(self):
        variants = {}
        variants['missing_column'] = self.annual.drop(columns='population')
        variants['duplicate'] = pd.concat([self.annual, self.annual.iloc[:1]], ignore_index=True)
        variants['missing_department'] = self.annual.iloc[1:].copy()
        for name, column, value in [
            ('zero_population', 'population', 0), ('negative_cases', 'cases_men5', -1),
            ('missing_count', 'death_men5', np.nan), ('invalid_year', 'year', 2023.5),
            ('unknown_year', 'year', 1999), ('invalid_code', 'iddpto', 99),
            ('missing_name', 'department', ''), ('invalid_rate', 'cases_rate_men5', 999),
            ('zero_cases_with_deaths', 'cases_men5', 0),
        ]:
            data = self.annual.copy()
            data[column] = data[column].astype(object)
            data.loc[0, column] = value
            variants[name] = data
        for name, data in variants.items():
            with self.subTest(name=name):
                self.write(self.annual_path, data)
                service = EpidemiologyDataService(self.root)
                self.assertTrue(service.get_annual_measures().empty)
                self.assertEqual(service.get_departments(), [])
                self.assertTrue(service.get_national_summary().empty)
                self.assertTrue(service.get_department_data('DEPARTAMENTO 1').empty)
                self.assertEqual(next(iter(service.reader.evidence.values()))['estado'], 'No válido')

    def test_zero_cases_is_not_zero_percent(self):
        for group in ('men5', '60mas'):
            for kind in ('cases', 'hosp', 'death'):
                self.annual[f'{kind}_{group}'] = 0
                self.annual[f'{kind}_rate_{group}'] = 0
        self.write(self.annual_path, self.annual)
        service = EpidemiologyDataService(self.root)
        national = service.get_national_summary()
        self.assertTrue(national['hr_men5'].isna().all())
        self.assertTrue(national['cfr_men5'].isna().all())
        self.assertTrue(service.get_department_data('DEPARTAMENTO 1')['cfr_men5'].isna().all())
        kpis = service.compute_kpis(national, year=2023)
        self.assertTrue(np.isnan(kpis['hr']))
        self.assertTrue(np.isnan(kpis['cfr']))
        self.assertEqual(kpis['cases'], 0)

    def test_missing_primary_uses_documented_alternative_but_not_corrupt_primary(self):
        alternative = self.root / 'outputs/tables' / self.annual_path.name
        self.write(alternative, self.annual)
        service = EpidemiologyDataService(self.root)
        self.assertFalse(service.get_annual_measures().empty)
        self.assertEqual(len(service.reader.evidence), 2)
        self.write(self.annual_path, self.annual.drop(columns='year'))
        service = EpidemiologyDataService(self.root)
        self.assertTrue(service.get_annual_measures().empty)
        self.assertEqual(len(service.reader.evidence), 1)

    def test_unreadable_csv_is_recorded(self):
        self.annual_path.parent.mkdir(parents=True)
        for payload in [b'', b'col\n"unfinished', b'\xff\xfe\xfd']:
            with self.subTest(payload=payload):
                self.annual_path.write_bytes(payload)
                service = EpidemiologyDataService(self.root)
                self.assertTrue(service.get_annual_measures().empty)
                self.assertEqual(next(iter(service.reader.evidence.values()))['estado'], 'No válido')

    def test_missing_metrics_and_importances_have_no_synthetic_values(self):
        service = EpidemiologyModelService(self.root)
        self.assertTrue(service.get_national_metrics().empty)
        self.assertTrue(service.get_feature_importance_summary().empty)
        self.assertTrue(service.get_national_future_predictions().empty)
        self.assertTrue(all(record['estado'] == 'No disponible' for record in service.reader.evidence.values()))

    def test_invalid_metrics_are_rejected_but_negative_r2_is_valid(self):
        for column, value in [('rmse', -1), ('mae', np.nan), ('r2', 1.1)]:
            with self.subTest(column=column):
                data = self.metrics.copy()
                data.loc[0, column] = value
                self.write(self.model_path('metrics'), data)
                self.assertTrue(EpidemiologyModelService(self.root).get_national_metrics().empty)
        self.metrics.loc[0, 'r2'] = -0.5
        self.write(self.model_path('metrics'), self.metrics)
        self.assertFalse(EpidemiologyModelService(self.root).get_national_metrics().empty)

    def test_missing_rmse_preserves_points_without_inventing_bands(self):
        self.write(self.model_path('future_predictions'), self.forecasts)
        service = EpidemiologyModelService(self.root)
        result = service.get_national_future_predictions()
        self.assertEqual(result.iloc[0]['predicted'], 2)
        self.assertTrue(result['lower_ci'].isna().all())
        self.assertEqual(result.attrs['missing_band_models'], ['xgboost'])
        self.metrics.loc[0, 'model'] = 'random_forest'
        self.write(self.model_path('metrics'), self.metrics)
        result = EpidemiologyModelService(self.root).get_national_future_predictions()
        self.assertTrue(result['upper_ci'].isna().all())

    def test_bands_use_the_matching_model_metric(self):
        self.write(self.model_path('future_predictions'), self.forecasts)
        self.write(self.model_path('metrics'), self.metrics)
        service = EpidemiologyModelService(self.root)
        result = service.get_national_future_predictions()
        self.assertAlmostEqual(result.iloc[0]['lower_ci'], 2 - 1.96 * 0.2)
        self.assertAlmostEqual(result.iloc[0]['upper_ci'], 2 + 1.96 * 0.2)
        self.assertEqual(result.attrs['missing_band_models'], [])
        evidence = service.reader.evidence[result.attrs['source']]
        self.assertIn('dependencias', evidence)

    def test_corrupt_forecasts_are_rejected(self):
        variants = []
        for column, value in [('date', 'invalid date'), ('predicted', np.inf), ('model', '')]:
            data = self.forecasts.copy()
            data.loc[0, column] = value
            variants.append(data)
        variants.append(pd.concat([self.forecasts, self.forecasts]))
        variants.append(self.forecasts.iloc[:-1].copy())
        gap = self.forecasts.copy()
        gap.loc[51, 'date'] = '2024-12-30'
        variants.append(gap)
        variants.append(self.forecasts.assign(lower_ci=1))
        variants.append(self.forecasts.assign(lower_ci=3, upper_ci=1))
        for data in variants:
            with self.subTest(columns=list(data.columns)):
                self.write(self.model_path('future_predictions'), data)
                self.assertTrue(EpidemiologyModelService(self.root).get_national_future_predictions().empty)

    def test_supplied_valid_bands_preserve_their_source(self):
        self.write(self.model_path('future_predictions'), self.forecasts.assign(lower_ci=1, upper_ci=3))
        service = EpidemiologyModelService(self.root)
        result = service.get_national_future_predictions()
        self.assertEqual(result.iloc[0]['upper_ci'], 3)
        self.assertIn('incluidas en el archivo', result.attrs['band_method'])
        self.assertEqual(len(service.reader.evidence), 1)

    def test_importance_selection_is_explicit_and_cannot_escape_folder(self):
        folder = self.root / 'outputs/children_feature_importance_ci'
        for name, value in [('a_xgboost_feature_importance.csv', 0.2), ('b_random_forest_feature_importance.csv', 0.8)]:
            self.write(folder / name, pd.DataFrame({'feature': ['lag_1'], 'importance': [value]}))
        service = EpidemiologyModelService(self.root)
        sources = service.get_feature_importance_sources()
        self.assertEqual(len(sources), 2)
        result = service.get_feature_importance_summary(source=sources[1])
        self.assertEqual(result.iloc[0]['importance'], 0.8)
        self.assertTrue(result.attrs['source'].endswith(sources[1]))
        with self.assertRaises(ValueError):
            service.get_feature_importance_summary(source='../fake.csv')
        self.write(folder / sources[0], pd.DataFrame({'feature': ['lag_1'], 'importance': [0]}))
        self.assertTrue(service.get_feature_importance_summary(source=sources[0]).empty)

    def test_invalid_ranking_does_not_affect_annual_data(self):
        self.write(self.annual_path, self.annual)
        path = self.root / 'outputs/tables/rank_grid_children_cases_rate.csv'
        for data in [pd.DataFrame({'region': ['A']}), pd.DataFrame({'region': ['A'], '2023': [99]})]:
            self.write(path, data)
            service = EpidemiologyDataService(self.root)
            self.assertTrue(service.get_rank_grid().empty)
            self.assertFalse(service.get_national_summary().empty)

    def test_report_export_contains_actual_sources_and_pending_evaluations(self):
        self.write(self.annual_path, self.annual)
        data = EpidemiologyDataService(self.root)
        models = EpidemiologyModelService(self.root)
        data.get_annual_measures()
        models.get_national_metrics()
        report = evidence_report(data, models, {'grupo': 'men5', 'periodo': [2023, 2023]})
        content = export_with_evidence(self.annual, report)
        with ZipFile(BytesIO(content)) as archive:
            self.assertEqual(set(archive.namelist()), {'datos.csv', 'fuentes_y_validaciones.json'})
            loaded = json.loads(archive.read('fuentes_y_validaciones.json'))
            self.assertEqual(loaded['seleccion']['grupo'], 'men5')
            self.assertEqual(len(loaded['evaluaciones_pendientes']), 5)
            self.assertEqual(loaded['archivos'][0]['sha256'], sha256(self.annual_path.read_bytes()).hexdigest())
            self.assertEqual(loaded['archivos'][1]['estado'], 'No disponible')

    def test_readers_have_isolated_evidence(self):
        self.write(self.annual_path, self.annual)
        first = EpidemiologyDataService(self.root)
        first.get_annual_measures()
        second = EpidemiologyDataService(self.root)
        self.assertEqual(second.reader.evidence, {})
        self.assertEqual(first.compute_kpis(pd.DataFrame()), {})

    def test_one_session_uses_one_file_version_and_next_session_revalidates(self):
        self.write(self.model_path('metrics'), self.metrics)
        service = EpidemiologyModelService(self.root)
        first = service.get_national_metrics()
        self.metrics.loc[0, 'rmse'] = 0.4
        self.write(self.model_path('metrics'), self.metrics)
        self.assertEqual(service.get_national_metrics().iloc[0]['rmse'], 0.2)
        new_session = EpidemiologyModelService(self.root)
        self.assertEqual(new_session.get_national_metrics().iloc[0]['rmse'], 0.4)
        self.assertNotEqual(service.reader.evidence[first.attrs['source']]['sha256'],
                            new_session.reader.evidence[first.attrs['source']]['sha256'])


if __name__ == '__main__':
    unittest.main()
