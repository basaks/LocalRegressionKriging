import numpy as np
from scipy.spatial import cKDTree
from pykrige import OrdinaryKriging, UniversalKriging
from sklearn.base import RegressorMixin, BaseEstimator

krige_methods = {'ordinary': OrdinaryKriging,
                 'universal': UniversalKriging}


class LocalRegressionKriging(RegressorMixin, BaseEstimator):
    def __init__(self,
                 xy,
                 regression_model,
                 kriging_model,
                 variogram_model,
                 num_points):
        """
        Parameters
        ----------
        xy: list
            list of (x, y) points for which  covariate values are required
        regression_model: sklearn compatible regression class
        kriging_model: str
            should be 'ordinary' or 'universal'
        variogram_model: str
            pykrige compatible variogram model
        num_points: int
            number of points for the local kriging
        """
        self.xy = xy
        self.regression = regression_model
        self.kriging_model = krige_methods[kriging_model]
        self.variogram_model = variogram_model
        self.num_points = num_points
        self.trained = False
        self.residual = np.zeros_like(self.xy)
        self.tree = cKDTree(self.xy)

    def fit(self, x, y, *args, **kwargs):
        self.regression.fit(x, y)
        self.residual = y - self.regression.predict(x)
        self.trained = True

    def predict(self, x, lat, lon, *args, **kwargs):
        """
        Parameters
        ----------
        x: np.array
            features of the regression model
        lat: float
            latitude
        lon: float
            longitude

        """
        if not self.trained:
            raise Exception('Not trained. Train first')

        reg_pred = self.regression.predict(x)
        d, ii = self.tree.query([lat, lon], self.num_points)

        xs = [self.xy[i][0] for i in ii]
        ys = [self.xy[i][1] for i in ii]
        zs = [self.residual[i] for i in ii]
        krige_class = self.kriging_model(xs, ys, zs, self.variogram_model)
        res, res_std = krige_class.execute('points', [lat], [lon])
        reg_pred += res  # local kriged residual correction

        # TODO: return std for regression models that support std

        return reg_pred