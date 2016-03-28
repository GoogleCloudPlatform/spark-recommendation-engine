#!/usr/bin/env python
"""
Copyright Google Inc. 2016
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from __future__ import print_function

import sys
import itertools
from math import sqrt
from operator import add
from os.path import join, isfile, dirname
from pyspark import SparkContext, SparkConf, SQLContext
from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel, Rating
from pyspark.sql.types import StructType
from pyspark.sql.types import StructField
from pyspark.sql.types import StringType
from pyspark.sql.types import FloatType

conf = SparkConf().setAppName("app_collaborative")
sc = SparkContext(conf=conf)
sqlContext = SQLContext(sc)

USER_ID = 0
#CLOUDSQL_INSTANCE_IP = 173.194.251.148
#BEST_RANK = 20
#BEST_ITERATION = 10
#BEST_REGULATION = 0.1

CLOUDSQL_INSTANCE_IP = sys.argv[1]
CLOUDSQL_DB_NAME = sys.argv[2]
CLOUDSQL_USER = sys.argv[3]
CLOUDSQL_PWD  = sys.argv[4]

BEST_RANK = int(sys.argv[5])
BEST_ITERATION = int(sys.argv[6])
BEST_REGULATION = float(sys.argv[7])

TABLE_ITEMS  = "Accommodation"
TABLE_RATINGS = "Rating"
TABLE_RECOMMENDATIONS = "Recommendation"

# Read the data from the Cloud SQL
# Create dataframes
#[START read_from_sql]
jdbcDriver = 'com.mysql.jdbc.Driver'
jdbcUrl    = 'jdbc:mysql://%s:3306/%s?user=%s&password=%s' % (CLOUDSQL_INSTANCE_IP, CLOUDSQL_DB_NAME, CLOUDSQL_USER, CLOUDSQL_PWD)
dfAccos = sqlContext.load(source='jdbc', driver=jdbcDriver, url=jdbcUrl, dbtable=TABLE_ITEMS)
dfRates = sqlContext.load(source='jdbc', driver=jdbcDriver, url=jdbcUrl, dbtable=TABLE_RATINGS)
#[END read_from_sql]

# Get all the ratings rows of our user
dfUserRatings  = dfRates.filter(dfRates.userId == USER_ID).map(lambda r: r.accoId).collect()
print(dfUserRatings)

# Returns only the accommodations that have not been rated by our user
rddPotential  = dfAccos.rdd.filter(lambda x: x[0] not in dfUserRatings)
pairsPotential = rddPotential.map(lambda x: (USER_ID, x[0]))

#[START split_sets]
rddTraining, rddValidating, rddTesting = dfRates.rdd.randomSplit([6,2,2])
#[END split_sets]

#[START predict]
# Build our model with the best found values
# Rating, Rank, Iteration, Regulation
model = ALS.train(rddTraining, BEST_RANK, BEST_ITERATION, BEST_REGULATION)

# Calculate all predictions
predictions = model.predictAll(pairsPotential).map(lambda p: (str(p[0]), str(p[1]), float(p[2])))

# Take the top 5 ones
topPredictions = predictions.takeOrdered(5, key=lambda x: -x[2])
print(topPredictions)

schema = StructType([StructField("userId", StringType(), True), StructField("accoId", StringType(), True), StructField("prediction", FloatType(), True)])

#[START save_top]
dfToSave = sqlContext.createDataFrame(topPredictions, schema)
dfToSave.write.jdbc(url=jdbcUrl, table=TABLE_RECOMMENDATIONS, mode='overwrite')
#[END save_top]