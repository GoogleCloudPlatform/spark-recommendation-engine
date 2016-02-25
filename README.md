# Recommendation on Google Cloud Platform
This tutorial shows how to run the code explained in the solution paper [Recommendation Engine on Google Cloud Platform](https://cloud.com/solutions/recommendations-using-machine-learning-on-compute-engine). In order to run this example fully you will need to use various components.

Disclaimer: This is not an official Google product.
## Setting up
### Before you begin
This tutorial assumes that you have a Cloud Platform project. To set up a project, please refer to the [relevant documentation](https://cloud.google.com/)

The main steps involved in this example are:

1. Setup a Spark cluster
2. Setup a simple App Engine website
3. Create a Cloud SQL database with an accommodation table, a rating table and a recommendation table.
4. Run a python script on our Spark cluster in order to find the best model
5. Run a python script making prediction using the best model
6. Saving the predictions into Cloud SQL so our user 0 can see them when displaying the welcome page

Google Cloud Platform offers various ways to deploy a Hadoop cluster to use Spark. In this documentation, we will describe two distinct ways:

* Using [bdutil](https://cloud.google.com/hadoop/bdutil), a command line tool that simplifies the cluster creation, deployment and the connectivity to Google Cloud Platform
* Using [Dataproc](https://cloud.google.com/dataproc), a managed service that makes running your custom code seamless thanks to its easy way to create a cluster, deploy Hadoop, connect to Google Cloud Platform components, submit jobs, scale the cluster and monitor the nodes, all that through a UI

The quickest and easiest way is to use Dataproc but we also describe the steps involved in bdutil.

### Setup using bdutil
#### Cluster
Follow these steps to set up Apache Spark:

1. Download bdutil from https://cloud.google.com/hadoop/downloads.
2. Change your environment values as shown here https://cloud.google.com/hadoop/bdutil  
  a. CONFIGBUCKET="you_root_bucket_name"  
  b. PROJECT="your-project"  
3. Deploy your cluster and log into the Hadoop master instance

```sh
./bdutil deploy -e extensions/spark/spark_env.sh
./bdutil shell
```

Notes :

* Using the bdutil shell is equivalent to using the SSH command-line interface to connect to the instance.
* bdutil uses Cloud Storage as a file system which means that all references to files are relative to the CONFIGBUCKET folder.

#### Setup the JDBC connector on the master
In order to be able to call the Python application file with the connector, download the [JDBC connector](http://dev.mysql.com/downloads/connector/j/) to your working folder on the master instance. After you install it, you can use the connector when calling the Python file through the spark-submit command line.

#### Setup the JDBC on each worker
Because each worker needs to access the data, download the JDBC connector onto each instance:

1. Download the connector to */usr/share/java*.
2. Add the following lines to */home/hadoop/spark-install/conf/spark-defaults.conf*. Don't forget to replace the names of the JAR files with the correct version.

```sh
spark.driver.extraClassPath /usr/share/java/mysql-connector-java-x.x.xx-bin.jar
spark.executor.extraClassPath /usr/share/java/mysql-connector-java-x.x.xx-bin.jar
```
### Setup using Dataproc
Setup a cluster with the default parameters as explained in the Dataproc documentation on [how to create a cluster](https://cloud.google.com/dataproc/create-cluster)
Dataproc does not require to setup the JDBC connector.
### Create and Configure Cloud SQL Access
Follow these [instructions](https://cloud.google.com/sql/docs/getting-started?hl=en#create) to create a Cloud SQL instance. 
To be make sure your Spark cluster can access your Cloud SQL database, you must:

* Whitelist the IPs of the nodes as explained in the [Cloud SQL documentation](https://cloud.google.com/sql/docs/access-control#appaccess). You can find the instances IPs by going to Compute Engine -> VM Instances. There you should see a number of instances (based on your cluster size) with names like *cluster*-m, *cluster*-w-*i* where cluster is the name of your cluster and i is a slave number.
* [Create an IPv4 address](https://cloud.google.com/sql/docs/access-control#appaccess) so the Cloud SQL instance can be accessed through the network.

## Example data
### Cloud SQL Data
After you [created and connected to an instance](https://cloud.google.com/sql/docs/getting-started), you will need to create some tables and load data in some of them following these steps:

1. Connect to your project Cloud SQL instance through the console
2. Create the database and tables as explained [here](https://cloud.google.com/sql/docs/import-export?hl=en#import-database) using the provided [sql script](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/sql/table_creation.sql). In the Cloud Storage file input, enter *solutions-public-assets/recommendation-spark/sql/table_creation.sql*
3. In the same way, populate the *Accommodation* and *Rating* tables using the provided [accommodations.csv](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/sql/accommodations.csv) and [ratings.csv](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/sql/ratings.csv).

![Accommodation import screenshot](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/accommodation_import_screenshot.png)

## Renting Website
This [appengine](appengine) folder contains a simple html website built with [Python on App Engine](https://cloud.google.com/appengine/docs/python/) using [Angular Material](https://material.angularjs.org). While it is not required to deploy this website, it gives an idea on what a recommendation display could look like in a production environment.

You can find some accomodation images [here](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/images.zip) and upload them to your own bucket to display them. Remember to update the <YOUR_IMAGE_BUCKET> in [app/template/welcome.html](app/template/welcome.html) page

## Recommendation scripts
The main part of this solution paper is explained on the Google Cloud Platform [solutions](https://cloud.google.com/solutions) page. In the pyspark [folder](pyspark), you will find the scripts mentionned in the [solution paper](https://cloud.com/solutions/recommendations-using-machine-learning-on-compute-engine):

* [find_model_collaborative.py](pyspark/find_model_collaborative.py)
* [app_collaborative.py](pyspark/app_collaborative.py)

Both scripts should be run in a Spark cluster. This can be done on Google Cloud Platform by either using [Dataproc](https://cloud.google.com/dataproc/) or [bdutil](https://cloud.google.com/hadoop/bdutil).
### Find the best model
#### Using bdutil on the master node
There are two ways to run code in Spark: through the command line or by loading a Python file. In this case, it's easier to use the Python file to avoid writing each line of code into the CLI. Remember to pass the path to the JDBC JAR file as a parameter so it can be used by the sqlContext.load function.

```sh
$ spark-submit \
  --driver-class-path mysql-connector-java-x.x.xx-bin.jar \
  --jars mysql-connector-java-x.x.xx-bin.jar \
  find_model_collaborative.py \
  <YOUR_CLOUDSQL_INSTANCE_IP> \
  <YOUR_CLOUDSQL_INSTANCE_NAME> \
  <YOUR_CLOUDSQL_USER> \
  <YOUR_CLOUDSQL_PASSWORD>
```
#### Using Dataproc
Dataproc already has the connector enabled so there is no need to set it up. 

The easiest way is to use the Cloud Console and run the script directly from a remote location (Cloud Storage for example). See the [documentation](https://cloud.google.com/dataproc/submit-job#using_the_console_name)

![Submit Find Model](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/job_submit.png)

It is also possible to simply run this command line from a local computer

```sh
$ gcloud beta dataproc jobs submit pyspark \
  --cluster <YOUR_DATAPROC_CLUSTER_NAME> \
  find_model_collaborative.py \
  <YOUR_CLOUDSQL_INSTANCE_IP> \
  <YOUR_CLOUDSQL_INSTANCE_NAME> \
  <YOUR_CLOUDSQL_USER> \
  <YOUR_CLOUDSQL_PASSWORD>
```

### Use the best found parameters
The script above will returned a combination of the best parameters for the ALS training as explained in the Training the model part of the paper. It will be displayed in the console in the following format where Dist represents how far we are from being the known value. The result might not feel satisfying but remember that our training dataset was quite small.

![Submit Find Model](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/result_find_model.png)

Once we have those values, we can reuse them when calling our recommendation script.

```sh
# Build our model with the best found values
model = ALS.train(rddTraining, BEST_RANK, BEST_ITERATION, BEST_REGULATION)
```
where - in our current case - BEST_RANK=15,  BEST_ITERATION=20,  BEST_REGULATION=0.1

### Make the prediction
We run the app_collaborative.py file with the updated values as we did above. The code will make prediction and save the top 5 expected rates in Cloud SQL (we will be able to look at the results later)
#### Using bdutil on the master

```sh
$ spark-submit \
  --driver-class-path mysql-connector-java-5.1.36-bin.jar \
  --jars mysql-connector-java-5.1.36-bin.jar \
  app_collaborative.py \
  <YOUR_CLOUDSQL_INSTANCE_IP> \
  <YOUR_CLOUDSQL_INSTANCE_NAME> \
  <YOUR_CLOUDSQL_USER> \
  <YOUR_CLOUDSQL_PASSWORD> \
  <YOUR_BEST_RANK> \
  <YOUR_BEST_ITERATION> \
  <YOUR_BEST_REGULATION>
```
#### Using Dataproc
You can use the Cloud console as explained above which would be equivalent of running the script below from your local computer.

```sh
$ gcloud beta dataproc jobs submit pyspark \
  --cluster <YOUR_DATAPROC_CLUSTER_NAME> \
  app_collaborative.py \
  <YOUR_CLOUDSQL_INSTANCE_IP> \
  <YOUR_CLOUDSQL_INSTANCE_NAME> \
  <YOUR_CLOUDSQL_USER> \
  <YOUR_CLOUDSQL_PASSWORD> \
  <YOUR_BEST_RANK> \
  <YOUR_BEST_ITERATION> \
  <YOUR_BEST_REGULATION>
```
### Results
#### See in the console
The code posted in github actually prints the top 5 predictions. You should see something similar to a list of tuples (userId, accoId, prediction) as displayed below.

```sh
[('0', '75', 4.6428704512729375), ('0', '76', 4.54325166163637), ('0', '86', 4.529177571208829), ('0', '66', 4.52387350189572), ('0', '99', 4.44705391172443)]
```  
#### Display the top recommendations saved in the Database
Running the following SQL query on the database will return the predictions saved in the Recommendation table by app_collaborative.py

```sh
SELECT 
  id, title, type, r.prediction 
FROM
  Accommodation a
INNER JOIN
  Recommendation r
ON
 r.accoId = a.id
WHERE
  r.userId = <USER_ID>
ORDER BY 
  r.prediction desc
```