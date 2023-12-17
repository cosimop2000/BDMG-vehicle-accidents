
import contextlib
import os

os.environ["PYARROW_IGNORE_TIMEZONE"] = "1"
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
import re
from typing import Union

import pandas as pd
import ast
from databricks.koalas import DataFrame, Series
from databricks.koalas.config import reset_option, set_option
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from src.algorithms.utils import timing
from src.datasets.dataset import Dataset
from pyspark.sql import SparkSession
from src.algorithms.algorithm import AbstractAlgorithm



class KoalasBench(AbstractAlgorithm):
    df_: Union[DataFrame, Series]
    backup_: Union[DataFrame, Series]
    ds_ : Dataset = None
    name = "koalas"
    
    def __init__(self, conf=None, master="", app_name="", jarPath=None, mem: str = None, cpu: int = None, **kwargs):

        self.mem_ = mem
        self.cpu_ = cpu
        import sys
        os.environ['PYSPARK_PYTHON'] = sys.executable
        os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
    
        if conf is None:
            conf = {}
        
        if type(conf) is str:
            import json
            conf = json.loads(conf)
            print(type(conf))
        
        self.c = SparkConf()
        print(conf)
        for k in conf:
            self.c.set(k, conf[k])
       
        print(conf)
        self.sparkSession = None
        if len(master) > 0:
            self.sparkSession = (
                SparkSession.builder.master(master)
                .appName(app_name)
                .config(conf=self.c)
                .getOrCreate()
            )
        else:
            self.sparkSession = (
                SparkSession.builder.appName(app_name).config(conf=self.c).getOrCreate()
            )
        
        """
        In this way koalas is imported by considering 
        the custom SparkConf
        """
        global ks
        import databricks.koalas as ks


    @timing        
    def get_pandas_df(self):
        return self.df_.to_pandas()
    @timing
    def load_from_pandas(self, df):
        self.df_ = ks.from_pandas(df)

    def backup(self):
        """
        Creates a backup copy of the current dataframe
        """
        self.backup_ = self.df_.copy()
        
    def restore(self):
        """
        Replace the internal dataframe with the backup
        """
        self.df_ = self.backup_.copy()
    
    @timing
    def load_dataset(self, ds: Dataset, conn=None, **kwargs):
        """
        Load the provided dataframe
        """
        self.ds_ = ds
        path = ds.dataset_attribute.path
        format = ds.dataset_attribute.type
        
        if format == "csv":
            self.df_ = self.read_csv(path, **kwargs)
        elif format == "excel":
            self.df_ = self.read_excel(path, **kwargs)
        elif format == "json":
            self.df_ = self.read_json(path, **kwargs)
        elif format == "parquet":
            self.df_ = self.read_parquet(path, **kwargs)
        elif format == "sql":
            self.df_ = self.read_sql(path, conn, **kwargs)

        elif format == "xml":
            self.df_ = self.read_xml(path, **kwargs)
            
        if "partition_col" in kwargs:
            self.df_ = self.df_.set_index(kwargs["partition_col"])
        return self.df_

    def read_sql(self, query, conn, **kwargs):
        """
        Given a connection and a query
        creates a dataframe from the query output
        """
        self.df_ = ks.read_sql(query, conn)
        return self.df_

    def read_json(self, path, **kwargs):
        """
        Read a json file
        """
        self.df_ = ks.read_json(path, **kwargs)
        return self.df_

    def read_csv(self, path, **kwargs):
        """
        Read a csv file
        """
        self.df_ = ks.read_csv(path, **kwargs)
        return self.df_

    def read_xml(self, path, **kwargs):
        """
        Read a xml file
        """
        self.df_ = ks.from_pandas(pd.read_xml(path, **kwargs))
        return self.df_

    def read_excel(self, path, **kwargs):
        """
        Read an excel file
        """
        self.df_ = ks.read_excel(path, **kwargs)
        return self.df_

    def read_parquet(self, path, **kwargs):
        """
        Read a parquet file
        """
        self.df_ = ks.read_parquet(path, **kwargs)
        return self.df_

    @timing
    def sort(self, columns, ascending=True):
        """
        Sort the dataframe by the provided columns
        Columns is a list of column names
        """
        self.df_ = self.df_.sort_values(columns, ascending=ascending)
        return self.df_

    @timing
    def get_columns(self):
        """
        Return the name of the columns in the dataframe
        """
        return list(self.df_.columns.values)

    @timing
    def is_unique(self, column):
        """
        Check the uniqueness of all values contained in the provided column_name
        """
        return self.df_[column].is_unique

    @timing
    def delete_columns(self, columns):
        """
        Delete the specified columns
        Columns is a list of column names
        """
        self.df_ = self.df_.drop(columns=columns)
        return self.df_
    
    @timing
    def rename_columns(self, columns):
        """
        Rename the provided columns using the provided names
        Columns is a dictionary: {"column_name": "new_name"}
        """
        self.df_ = self.df_.rename(columns=columns)
        return self.df_

    @timing
    def merge_columns(self, columns, separator, name):
        """
        Create a new column with the provided name combining the two provided columns using the provided separator
        Columns is a list of two column names; separator and name are strings
        """
        self.df_[name] = (
            self.df_[columns[0]].astype(str)
            + separator
            + self.df_[columns[1]].astype(str)
        )
        return self.df_

    @timing
    def fill_nan(self, value, columns=None):
        """
        Fill nan values in the dataframe with the provided value
        :param value value to use for replacing null values
        :columns columns to fill, if empty all the dataframe is filled
        """
        if columns is None:
            columns = []
        if len(columns) == 0:
            self.df_ = self.df_.fillna(value)
        else:
            for c in columns:
                self.df_[c] = self.df_[c].fillna(value)
        return self.df_

    @timing
    def one_hot_encoding(self, columns):
        """
        Performs one-hot encoding of the provided columns
        Columns is a list of column names
        """
        dummies = ks.get_dummies(self.df_[columns])
        self.df_ = ks.concat([self.df_.drop(columns=columns), dummies], axis=1)
        return self.df_

    @timing
    def locate_null_values(self, column):
        """
        Returns the rows of the dataframe which contains
        null value in the provided column.
        """
        return self.df_[self.df_[column].isna()]

    @timing
    def search_by_pattern(self, column, pattern):
        """
        Returns the rows of the dataframe which
        match with the provided pattern
        on the provided column.
        Pattern could be a regular expression.
        """
        return self.df_[self.df_[column].str.contains(re.compile(pattern))]

    @timing
    def locate_outliers(self, column, lower_quantile=0.1, upper_quantile=0.99):
        """
        Returns the rows of the dataframe that have values
        in the provided column lower or higher than the values
        of the lower/upper quantile.
        """
        q_low = self.df_[column].quantile(lower_quantile)
        q_hi = self.df_[column].quantile(upper_quantile)
        return self.df_[(self.df_[column] < q_low) | (self.df_[column] > q_hi)]

    @timing
    def get_columns_types(self):
        """
        Returns a dictionary with column types
        """
        return self.df_.dtypes.apply(lambda x: x.name).to_dict()

    @timing
    def cast_columns_types(self, dtypes):
        """
        Cast the data types of the provided columns
        to the provided new data types.
        dtypes is a dictionary that provide for each
        column to cast the new data type.
        """
        self.df_ = self.df_.astype(dtypes)
        return self.df_

    @timing
    def get_stats(self):
        """
        Returns dataframe statistics.
        Only for numeric columns.
        Min value, max value, average value, standard deviation, and standard quantiles.
        """
        return self.df_.describe()

    def find_mismatched_dtypes(self):
        """
        Returns, if exists, a list of columns with mismatched data types.
        For example, a column with string dtypes that contains only integer values.
        For every columns the list contain an object with three keys:
         - Col: name of the column
         - current_dtype: current data type
         - suggested_dtype: suggested data type
        """
        current_dtypes = self.get_columns_types()

        df2 = self.df_.copy()
        df2 = df2.fillna("a")
        for c in df2.columns.values:
            with contextlib.suppress(Exception):
                df2[c] = ks.to_numeric(df2[c])
        new_dtypes = df2.dtypes.apply(lambda x: x.name).to_dict()

        return [{"col": k, "current_dtype": current_dtypes[k], "suggested_dtype": new_dtypes[k],} 
                for k in current_dtypes.keys() 
                if (new_dtypes[k] != current_dtypes[k]) and (not df2[k].isna().any())]

    @timing
    def check_allowed_char(self, column, pattern):
        """
        Return true if all the values of the provided column
        follow the provided pattern.
        For example, if the pattern [a-z] is provided the string
        'ciao' will return true, the string 'ciao123' will return false.
        """
        return self.df_[column].str.contains(re.compile(pattern)).all()

    @timing
    def drop_duplicates(self):
        """
        Drop duplicate rows.
        """
        self.df_ = self.df_.drop_duplicates()
        return self.df_

    @timing
    def drop_by_pattern(self, column, pattern):
        """
        Delete the rows where the provided pattern
        occurs in the provided column.
        """
        self.df_ = self.df_[~self.df_[column].str.contains(re.compile(pattern))]
        return self.df_

    @timing
    def change_date_time_format(self, column, str_date_time_format):
        """
        Change the date/time format of the provided column
        according to the provided formatting string.
        column datatype must be datetime
        An example of str_date_time_format is '%m/%d/%Y'
        """
        self.df_[column] = self.df_[column].dt.strftime(str_date_time_format)
        return self.df_

    @timing
    def set_header_case(self, case):
        """
        Put dataframe headers in the provided case
        Supported cases: "lower", "upper", "title", "capitalize", "swapcase"
        (see definitions in pandas documentation)
        """
        if case == "lower":
            self.df_.columns = map(str.lower, self.df_.columns)
        elif case == "upper":
            self.df_.columns = map(str.upper, self.df_.columns)
        elif case == "title":
            self.df_.columns = map(str.title, self.df_.columns)
        elif case == "capitalize":
            self.df_.columns = map(str.capitalize, self.df_.columns)
        elif case == "swapcase":
            self.df_.columns = map(str.swapcase, self.df_.columns)
        return self.df_

    @timing
    def set_content_case(self, columns, case):
        """
        Put dataframe content in the provided case
        Supported cases: "lower", "upper", "title", "capitalize", "swapcase"
        (see definitions in pandas documentation)
        Columns is a list of two column names; empty list for the whole dataframe
        """
        if len(columns) == 0:
            columns = list(self.df_.columns.values)
        for column in columns:
            if case == "lower":
                self.df_[column] = self.df_[column].str.lower()
            elif case == "upper":
                self.df_[column] = self.df_[column].str.upper()
            elif case == "title":
                self.df_[column] = self.df_[column].str.title()
            elif case == "capitalize":
                self.df_[column] = self.df_[column].str.capitalize()
            elif case == "swapcase":
                self.df_[column] = self.df_[column].str.swapcase()
        return self.df_

    @timing
    def duplicate_columns(self, columns):
        """
        Duplicate the provided columns (add to the dataframe with "_duplicate" suffix)
        Columns is a list of column names
        """
        for column in columns:
            self.df_[column + "_duplicate"] = self.df_[column]
        return self.df_

    @timing
    def pivot(self, index, columns, values, aggfunc):
        """
        Define the lists of columns to be used as index, columns and values respectively,
        and the dictionary to aggregate ("sum", "mean", "count") the values for each column: {"col1": "sum"}
        (see pivot_table in pandas documentation)
        """
        self.df_ = self.df_.pivot_table(
            index=index, values=values, columns=columns, aggfunc=aggfunc
        ).reset_index()
        return self.df_

    @timing
    def unpivot(self, columns, var_name, val_name):
        """
        Define the list of columns to be used as values for the variable column,
        the name for variable columns and the one for value column_name
        """
        self.df_ = self.df_.melt(
            id_vars=list(set(list(self.df_.columns.values)) - set(columns)),
            value_vars=columns,
            var_name=var_name,
            value_name=val_name,
        )
        return self.df_

    @timing
    def delete_empty_rows(self, columns):
        """
        Delete the rows with null values for all provided Columns
        Columns is a list of column names
        """
        self.df_.dropna(subset=columns, inplace=True)
        return self.df_

    @timing
    def split(self, column, sep, splits, col_names):
        """
        Split the provided column into splits + 1 columns named after col_names
        using the provided sep string as separator
        Col_names is a list of column names
        """
        self.df_[col_names] = self.df_[column].str.split(sep, splits, expand=True)
        return self.df_

    @timing
    def strip(self, columns, chars):
        """
        Remove the characters appearing in chars at the beginning/end of the provided columns
        Columns is a list of column names
        """
        for column in columns:
            self.df_[column] = self.df_[column].str.strip(chars)
        return self.df_

    @timing
    def remove_diacritics(self, columns):
        """
        Remove diacritics from the provided columns
        Columns is a list of column names
        """
        for column in columns:
            self.df_[column] = self.df_[column].str.normalize("NFKD")
            self.df_[column] = self.df_[column].apply(
                lambda x: x.encode("ascii", errors="ignore").decode("utf-8")
            )
        return self.df_

    @timing
    def set_index(self, column):
        """
        Set the provided column as index
        """
        self.df_ = self.df_.set_index(column)
        return self.df_

    @timing
    def change_num_format(self, formats):
        """
        Round one ore more columns to a variable number of decimal places.
        formats is a dictionary with the column names as key and the number of decimal places as value.
        """
        self.df_ = self.df_.round(formats)
        return self.df_

    @timing
    def calc_column(self, col_name, f):
        """
        Calculate the new column col_name by applying
        the function f
        """
        set_option("compute.ops_on_diff_frames", True)
        self.df_[col_name] = self.df_.apply(f, axis=1)
        reset_option("compute.ops_on_diff_frames")
        return self.df_

    @timing
    def join(self, other, left_on=None, right_on=None, how="inner", **kwargs):
        """
        Joins current dataframe (left) with a new one (right).
        left_on/right_on are the keys on which perform the equijoin
        how is the type of join
        **kwargs: additional parameters

        The result is stored in the current dataframe.
        """
        self.df_ = self.df_.merge(
            other, left_on=left_on, right_on=right_on, how=how, **kwargs
        )
        return self.df_

    @timing
    def groupby(self, columns, f):
        """
        Aggregate the dataframe by the provided columns
        then applied the function f on every group
        """
        return self.df_.groupby(columns).agg(f)

    @timing
    def categorical_encoding(self, columns):
        """
        Convert the categorical values in these columns into numerical values
        Columns is a list of column names
        """
        for column in columns:
            self.df_[column] = self.df_[column].astype("category")
            self.df_[column] = self.df_[column].cat.codes
        return self.df_

    @timing
    def sample_rows(self, frac, num):
        """
        Return a sample of the rows of the dataframe
        Frac is a boolean:
        - if true, num is the percentage of rows to be returned
        - if false, num is the exact number of rows to be returned
        """
        if frac:
            return self.df_.sample(frac=num / 100)
        f = num / len(self.df_)
        print(
            "warning koalas do not support exact num sample, only frac is supported"
        )
        return self.df_.sample(frac=f)

    @timing
    def append(self, other, ignore_index):
        """
        Append the rows of another dataframe (other) at the end of the provided dataframe
        All columns are kept, eventually filled by nan
        Ignore index is a boolean: if true, reset row indices
        """
        self.df_ = self.df_.append(other, ignore_index=ignore_index)
        return self.df_

    @timing
    def replace(self, columns, to_replace, value, regex):
        """
        Replace all occurrencies of to_replace (numeric, string, regex, list, dict) in the provided columns using the provided value
        Regex is a boolean: if true, to_replace is interpreted as a regex
        Columns is a list of column names
        """
        #!warning: koalas do not support regex in replace
        print("warning: koalas do not support regex in replace")
        self.df_[columns] = self.df_[columns].replace(
            to_replace=to_replace, value=value
        )
        return self.df_

    @timing
    def edit(self, columns, func:str, rolling:int = 1):
        """
        Edit the values of the cells in the provided columns using the provided expression
        Columns is a list of column names
        """
        set_option("compute.ops_on_diff_frames", True) 
    

        func = eval(func)
        for c in columns:
            self.df_[c] = self.df_[c].transform(func)
        reset_option("compute.ops_on_diff_frames")
        return self.df_

    @timing
    def set_value(self, index, column, value):
        """
        Set the cell identified by index and column to the provided value
        """
        self.df_.loc[index, column] = value
        return self.df_

    @timing
    def min_max_scaling(self, columns, min, max):
        """
        Independently scale the values in each provided column in the range (0, 1)
        Columns is a list of column names
        """
        for column in columns:
            self.df_[column] = self.df_[column] - self.df_[column].min()
            self.df_[column] = self.df_[column] / self.df_[column].max()
            self.df_[column] = self.df_[column] * (max - min) + min
        return self.df_

    @timing
    def round(self, columns, n):
        """
        Round the values in columns using n decimal places
        Columns is a list of column names
        """
        self.df_[columns] = self.df_[columns].round(n)
        return self.df_

    @timing
    def get_duplicate_columns(self):
        """
        Return a list of duplicate columns, if exists.
        Duplicate columns are those which have same values for each row.
        """
        cols = self.df_.columns.values
        return [(cols[i], cols[j]) 
                for i in range(len(cols)) 
                for j in range(i + 1, len(cols)) 
                if self.df_[cols[i]].equals(self.df_[cols[j]]).all()]

    @timing
    def to_csv(self, path, **kwargs):
        """
        Export the dataframe in a csv file.
        """
        self.df_.to_csv(path, **kwargs)

    @timing
    def query(self, query):
        """
        Queries the dataframe and returns the corresponding
        result set.
        :param query: a string with the query conditions, e.g. "col1 > 1 & col2 < 10"
        :return: subset of the dataframe that correspond to the selection conditions
        """
        return self.df_.query(query)

    @timing   
    def done(self):
        self.sc.stop()
    
    def force_execution(self):
        self.df_.to_pandas()

    
    def set_construtor_args(self, args):
        return args
