from sklearn.metrics import silhouette_score

from src.models.kmeans_model import get_anomaly_mask, predict_kmeans, train_kmeans


def test_kmeans_returns_fitted_model(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    assert hasattr(model, "labels_")
    assert model.n_clusters == 2


def test_kmeans_predict_shape(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    predictions = predict_kmeans(model, small_X)
    assert predictions.shape == (len(small_X),)


def test_kmeans_predict_valid_labels(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    predictions = predict_kmeans(model, small_X)
    assert set(predictions).issubset({0, 1})


def test_kmeans_separates_two_clusters(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    predictions = predict_kmeans(model, small_X)
    score = silhouette_score(small_X, predictions)
    assert score > 0.7


def test_get_anomaly_mask_dtype(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    predictions = predict_kmeans(model, small_X)
    mask = get_anomaly_mask(predictions, 0)
    assert mask.dtype == bool


def test_get_anomaly_mask_count(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    predictions = predict_kmeans(model, small_X)
    mask = get_anomaly_mask(predictions, 0)
    assert mask.sum() == (predictions == 0).sum()
