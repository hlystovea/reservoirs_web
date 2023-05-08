import datetime as dt

import numpy as np
import pandas as pd
from celery.utils.log import get_task_logger
from django.db import DatabaseError
from pytorch_forecasting import TemporalFusionTransformer as TFT

from predictors.models import WaterSituationForecast, WaterSituationPredictor
from weather.models import Weather

logger = get_task_logger(__name__)


class InflowForecastWorker:
    def __init__(self, predictor: WaterSituationPredictor):
        self.predictor = predictor
        self._model = None
        self.model: TFT = self._get_model()

    def _get_model(self) -> TFT:
        if self._model is None:
            self._model = TFT.load_from_checkpoint(self.predictor.checkpoint)
        return self._model

    def get_situation_data(self) -> pd.DataFrame:
        max_encoder_length = self.model.hparams['max_encoder_length']

        situations = self.predictor.reservoir.situations.filter(
            date__gte=dt.date.today() - dt.timedelta(days=max_encoder_length)
        ).order_by(
            'date'
        )
        return pd.DataFrame.from_records(situations.values())

    def get_weather_data(self) -> pd.DataFrame:
        max_encoder_length = self.model.hparams['max_encoder_length']

        weathers = Weather.objects.filter(
            geo_object__in=self.predictor.geo_objects.all(),
            date__date__gte=dt.date.today() - dt.timedelta(days=max_encoder_length)  # noqa(E501)
        ).order_by(
            'date'
        )
        return pd.DataFrame.from_records(weathers.values())

    @staticmethod
    def aggregate_weather(weather: pd.DataFrame) -> pd.DataFrame:
        return weather.groupby(['date', 'geo_object_id']).agg(
            {
                'temp': 'mean',
                'precipitation': 'sum',
            }
        ).reset_index()

    @staticmethod
    def add_features(weather: pd.DataFrame) -> pd.DataFrame:
        geo_object_ids = weather['geo_object_id'].unique()
        dates = weather['date'].unique()

        result = pd.DataFrame(dates, columns=['date'])

        for id in geo_object_ids:
            data = weather[weather['geo_object_id'] == id]
            data = data.drop('geo_object_id', axis=1)
            data.columns = ['date', f'temp_{id}', f'precipitation_{id}']
            result = result.merge(data, on='date', how='outer')

        return result

    def prepare_weather(self, weather_data: pd.DataFrame):
        return self.add_features(self.aggregate_weather(weather_data))

    @staticmethod
    def get_observed_weather(weather_data: pd.DataFrame) -> pd.DataFrame:
        return weather_data[weather_data.is_observable == 1]

    @staticmethod
    def get_forecasted_weather(weather_data: pd.DataFrame) -> pd.DataFrame:
        return weather_data[weather_data.is_observable != 1]

    def get_encoder_data(self, situation_data, weather_data) -> pd.DataFrame:
        observed_weather = self.get_observed_weather(weather_data)
        prepared_weather = self.prepare_weather(observed_weather)
        return situation_data.merge(prepared_weather, on='date', how='left')

    def get_decoder_data(self, weather_data, last_date) -> pd.DataFrame:
        forecasted_weather = self.get_forecasted_weather(weather_data)
        prepared_weather = self.prepare_weather(forecasted_weather)
        return prepared_weather.loc[prepared_weather['date'] > last_date]

    def get_prediction_data(self) -> pd.DataFrame:
        weather_data = self.get_weather_data()
        weather_data.date = weather_data.date.dt.date
        situation_data = self.get_situation_data()

        encoder_data = self.get_encoder_data(situation_data, weather_data)
        decoder_data = self.get_decoder_data(
            weather_data, encoder_data.date.max())

        prediction_data = pd.concat(
            [encoder_data, decoder_data],
            ignore_index=True
        )

        prediction_data['reservoir_id'] = 1
        prediction_data = prediction_data.astype({'reservoir_id': 'str'})
        prediction_data['time_idx'] = prediction_data.index
        prediction_data['doy'] = prediction_data.apply(
            lambda x: x['date'].timetuple().tm_yday, axis=1)

        return prediction_data.fillna(method='ffill')

    def save(self, date: dt.date, inflow: int) -> bool:
        try:
            _, created = WaterSituationForecast.objects.update_or_create(
                date=date,
                reservoir=self.predictor.reservoir,
                defaults={'inflow': inflow}
            )
            return created
        except DatabaseError as error:
            logger.error(f'{self.__class__.__name__} {repr(error)}')
            return False

    def predict(self):
        logger.info(f'{self.__class__.__name__} start forecasting')

        prediction_data = self.get_prediction_data()
        prediction_data.info()
        raw_predictions = self.model.predict(prediction_data, mode='raw')
        output_size = self.model.hparams['output_size']

        inflows = np.rint(
            raw_predictions.output['prediction'][0][:, output_size//2]
        ).numpy()

        date = prediction_data.date.values[-len(inflows)]
        saved_count = 0

        for inflow in inflows:
            saved = self.save(date, inflow)
            date += dt.timedelta(days=1)
            saved_count += saved

        logger.info(f'{self.__class__.__name__} saved {saved_count} new objs')


def water_situation_forecasting():
    predictors = WaterSituationPredictor.objects.all()

    for predictor in predictors:
        forecast_worker = InflowForecastWorker(predictor)
        forecast_worker.predict()
