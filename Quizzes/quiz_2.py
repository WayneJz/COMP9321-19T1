from pandas import DataFrame
from scipy.stats import zscore

# Question 1, Answer: C
data_1 = {'lkey': ['foo', 'bar', 'baz', 'foo'], 'value': [1, 2, 3, 5]}
data_2 = {'rkey': ['foo', 'bar', 'baz', 'foo'], 'value': [5, 6, 7, 8]}

df1 = DataFrame(data=data_1)
df2 = DataFrame(data=data_2)

df1 = df1.merge(df2, left_on='lkey', right_on='rkey', suffixes=('_left', '_right'))
print(df1)

# Question 2, Answer: A
data_3 = {'a': [1, 2, 3], 'b': [4, 5, 6], 'c': [7, 8, 9], 'd': [8, 8, 8], 'e': [7, 3, 2]}
df = DataFrame(data=data_3)
df = df.apply(zscore)
print(df)