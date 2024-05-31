# Packages

##pd  
###functions:
read_dir_files(directory=None, nameroot=None, extention=None, encoding='utf-8', sep=',')  
Czyta pliki i próbuje załadować treść do pd.DataFrame

merge_cols(df: pd.DataFrame, columns, target_column, func=None)  
Łączy kolumny używając zdeklarowanej funkcji (func)

apply_nan(data: Union[np.ndarray, pd.DataFrame], nan: Any)
Changes declared value into numpy.nan in pandas.DataFrame or a numpy.ndarray

