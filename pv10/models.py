"""On bir regresyon algoritmasi - hiperparametreler makaleyle birebir ayni.

Hiperparametreler onceden sabitlenmistir ve validasyon/test sonuclarina gore
ayarlanmaz. Bu kasitli bir tercihtir: iyimser yanlilik yaratmamak icin.
"""

from __future__ import annotations

from sklearn.ensemble import (ExtraTreesRegressor, GradientBoostingRegressor,
                              HistGradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge, SGDRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor

from .config import SEED

# Agac tabanli modeller olceklemeye ihtiyac duymaz ama imputasyona duyar;
# yine de tek bir on-isleme hatti kullanmak varyantlar arasi
# karsilastirilabilirligi korur.
ONISLEME = [("imp", SimpleImputer(strategy="median")),
            ("olc", StandardScaler())]


def _hat(tahminci, ek=None, onisleme: bool = True) -> Pipeline:
    adimlar = (list(ONISLEME) if onisleme else []) + list(ek or []) \
              + [("model", tahminci)]
    return Pipeline(adimlar)


def modeller(onisleme: bool = True) -> dict[str, Pipeline]:
    """Ad -> sklearn Pipeline. Her cagride yeni nesneler dondurur.

    onisleme=False verildiginde imputasyon ve olcekleme hattin DISINDA
    yapilmis demektir. Bu yalnizca "olcekleyici tum veriye fit edildi"
    sizinti varyanti icin kullanilir - kasitli bir kotu pratiktir.
    """
    _h = lambda t, ek=None: _hat(t, ek, onisleme)
    return {
        "Linear Regression": _h(LinearRegression()),

        "Polynomial Ridge": _h(
            Ridge(alpha=10.0, random_state=SEED),
            ek=[("poly", PolynomialFeatures(degree=2, include_bias=False))]),

        "SGD Regression": _h(
            SGDRegressor(random_state=SEED, max_iter=2000, tol=1e-4)),

        "K-Nearest Neighbours": _h(
            KNeighborsRegressor(n_neighbors=15, weights="distance", n_jobs=-1)),

        "Support Vector Regression": _h(
            SVR(kernel="rbf", C=30.0, epsilon=5.0)),

        "Decision Tree": _h(
            DecisionTreeRegressor(max_depth=18, random_state=SEED)),

        "Random Forest": _h(
            RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                  random_state=SEED, n_jobs=-1)),

        "Extra Trees": _h(
            ExtraTreesRegressor(n_estimators=400, min_samples_leaf=2,
                                random_state=SEED, n_jobs=-1)),

        "Gradient Boosting": _h(
            GradientBoostingRegressor(n_estimators=300, learning_rate=0.04,
                                      max_depth=3, random_state=SEED)),

        "Hist Gradient Boosting": _h(
            HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          random_state=SEED)),

        "Neural Network": _h(
            MLPRegressor(hidden_layer_sizes=(96, 48), early_stopping=True,
                         max_iter=500, random_state=SEED)),
    }


# --- hesaplama gercekligi -------------------------------------------------
# 350 bin satir x 25 oznitelikte:
#   Linear / Polynomial Ridge / Hist Gradient Boosting  -> saniyeler
#   Random Forest, Extra Trees (400 agac), MLP          -> dakikalar, cok RAM
#   SVR (O(n^2) kernel)                                 -> pratikte imkansiz
# Ablasyon izgarasi 6 varyant x 8 yil x N model demek; agir modelleri
# izgaranin her hucresinde kosmak haftalar surer.
ABLASYON_ALTKUMESI = ("Linear Regression", "Polynomial Ridge",
                      "Hist Gradient Boosting", "Random Forest", "Neural Network")

# Duman testi ve hizli iterasyon icin: hepsi saniyeler mertebesinde
HIZLI_ALTKUME = ("Linear Regression", "Polynomial Ridge", "Hist Gradient Boosting")