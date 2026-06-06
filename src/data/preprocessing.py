from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

def prepare_clustering_data(train_df, test_df):
    drop_colum