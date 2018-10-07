# Recommendation on Google Cloud Platform

This tutorial shows how to run the code explained in the solution paper [Recommendation Engine on Google Cloud Platform](https://cloud.google.com/solutions/recommendations-using-machine-learning-on-compute-engine). In order to run this example fully you will need to use various components.

Disclaimer: This is not an official Google product.

## Setting up

### Before you begin

This tutorial assumes that you have a Cloud Platform project. To set up a project:

1. In the Cloud Platform Console, go to the [Projects page](https://console.cloud.google.com/project).
1. Select a project, or click **Create Project** to create a new Cloud Platform Console project.
1. In the dialog, name your project. Make a note of your generated project ID.
1. Click **Create** to create a new project.

The main steps involved in this example are:

1. Setup a Spark cluster.
2. Setup a simple Google App Engine website.
3. Create a Cloud SQL database with an accommodation table, a rating table and a recommendation table.
4. Run a Python script on the Spark cluster to find the best model.
5. Run a Python script making a prediction using the best model.
6. Saving the predictions into Cloud SQL so the user can see them when displaying the welcome page.

The recommended approach to run Spark on Google Cloud Platform is to use [Google Cloud Dataproc](https://cloud.google.com/dataproc). Dataproc is a managed service that facilitates common tasks such as cluster deployment, jobs submissions, cluster scale and nodes monitoring. Interaction with Dataproc can be done over a UI, CLI or API.

### Setup using Cloud Dataproc

Set up a cluster with the default parameters as explained in the Cloud Dataproc documentation on [how to create a cluster](https://cloud.google.com/dataproc/create-cluster).
Cloud Dataproc does not require you to setup the JDBC connector.

### Create and Configure Google Cloud SQL (First Generation) Access

Follow [these instructions](https://cloud.google.com/sql/docs/getting-started?hl=en#create) to create a Cloud SQL instance. We will use a Cloud SQL first generation in this example.
To be make sure your Spark cluster can access your Cloud SQL database, you must:

* Whitelist the IPs of the nodes as explained in the [Cloud SQL documentation](https://cloud.google.com/sql/docs/external#appaccessIP). You can find the instances' IPs by going to **Compute Engine** -> **VM Instances** in the Cloud Console. There you should see a number of instances (based on your cluster size) with names like *cluster*-m, *cluster*-w-*i* where `cluster` is the name of your cluster and `i` is a slave number.
* [Create an IPv4 address](https://cloud.google.com/sql/docs/access-control#appaccess) so the Cloud SQL instance can be accessed through the network.
* Create a non-root user account. Make sure that this user account can connect from the IPs corresponding to the Dataproc cluster (not just localhost)

## Example data
### Cloud SQL Data

After you [create and connect to an instance](https://cloud.google.com/sql/docs/getting-started), you need to create some tables and load data into some of them by following these steps:

1. Connect to your project Cloud SQL instance through the Cloud Console.
2. Create the database and tables as explained [here](https://cloud.google.com/sql/docs/import-export?hl=en#import-database), using the provided [sql script](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/sql/table_creation.sql). In the Cloud Storage file input, enter `solutions-public-assets/recommendation-spark/sql/table_creation.sql`. If for some reason, the UI says that you have no access, you can also copy the file to your own bucket. In a CloudShell window or in a terminal type `gsutil cp gs://solutions-public-assets/recommendation-spark/sql/table_creation.sql gs://<your-bucket>/recommendation-spark/sql/table_creation.sql`.  Then, in the Cloud SQL import window, provide `<your-bucket>/recommendation-spark/sql/table_creation.sql` (i.e the path to your copy of the file on Google Storage, without the gs:// prefix).
3. In the same way, populate the *Accommodation* and *Rating* tables using the provided [accommodations.csv](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/sql/accommodations.csv) and [ratings.csv](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/sql/ratings.csv).

![Accommodation import screenshot](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/accommodation_import_screenshot.png)

## Renting Website

The [appengine](appengine) folder contains a simple HTML website built with [Python on App Engine](https://cloud.google.com/appengine/docs/python/) using [Angular Material](https://material.angularjs.org). While it is not required to deploy this website, it can give you an idea of what a recommendation display could look like in a production environment.

From the [appengine](/appengine) folder you can run

```
gcloud app deploy --project [YOUR-PROJECT-ID]
```

Make sure to update your database values in the [main.py](appengine/main.py) file to match your setup. If you kept the values of the .sql script, _DB_NAME = 'recommendation_spark'. The rest will be specific to your setup.

You can find some accommodation images [here](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/images.zip). Upload the individual files to your own bucket and change their acl to be public in order to serve them out. Remember to replace `<YOUR_IMAGE_BUCKET>` in [appengine/app/templates/welcome.html](appengine/app/templates/welcome.html) page with your bucket.


## Recommendation scripts

The main part of this solution paper is explained on the [Cloud Platform solution page](https://cloud.google.com/solutions/recommendations-using-machine-learning-on-compute-engine). In the `pyspark` [folder](pyspark), you will find the scripts mentionned in the [solution paper](https://cloud.com/solutions/recommendations-using-machine-learning-on-compute-engine):

* [find_model_collaborative.py](pyspark/find_model_collaborative.py)
* [app_collaborative.py](pyspark/app_collaborative.py)

Both scripts should be run in a Spark cluster. This can be done by using Cloud Dataproc.

### Find the best model
Dataproc already has the MySQL connector enabled so there is no need to set it up.

The easiest way is to use the Cloud Console and run the script directly from a remote location (Cloud Storage for example). See the [documentation](https://cloud.google.com/dataproc/submit-job#using_the_console_name).

![Submit Find Model](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/job_submit.png)

It is also possible to run this command line from a local computer:

```
$ gcloud dataproc jobs submit pyspark \
  --cluster <YOUR_DATAPROC_CLUSTER_NAME> \
  find_model_collaborative.py \
  -- <YOUR_CLOUDSQL_INSTANCE_IP> \
  <YOUR_CLOUDSQL_DB_NAME> \
  <YOUR_CLOUDSQL_USER> \
  <YOUR_CLOUDSQL_PASSWORD>
```

### Use the best found parameters

The script above returns a combination of the best parameters for the ALS training, as explained in the [Training the model](https://cloud.google.com/solutions/recommendations-using-machine-learning-on-compute-engine#Training-the-models) part of the solution article. It will be displayed in the console in the following format, where `Dist` represents how far we are from being the known value. The result might not feel satisfying but remember that the training dataset was quite small.

![Submit Find Model](https://storage.googleapis.com/solutions-public-assets/recommendation-spark/imgs/result_find_model.png)

After you have those values, you can reuse them when calling the recommendation script.

```
# Build our model with the best found values
model = ALS.train(rddTraining, BEST_RANK, BEST_ITERATION, BEST_REGULATION)
```
Where, in our current case, BEST_RANK=15,  BEST_ITERATION=20,  BEST_REGULATION=0.1.

### Make the prediction

Run the `app_collaborative.py` file with the updated values as you did before. The code  makes a prediction and saves the top 5 expected rates in Cloud SQL. You can look at the results later.

You can use the Cloud Console, as explained before, which would be equivalent of running the following script from your local computer.

```
$ gcloud dataproc jobs submit pyspark \
  --cluster <YOUR_DATAPROC_CLUSTER_NAME> \
  app_collaborative.py \
  -- <YOUR_CLOUDSQL_INSTANCE_IP> \
  <YOUR_CLOUDSQL_DB_NAME> \
  <YOUR_CLOUDSQL_USER> \
  <YOUR_CLOUDSQL_PASSWORD> \
  <YOUR_BEST_RANK> \
  <YOUR_BEST_ITERATION> \
  <YOUR_BEST_REGULATION>
```

### Results
#### See in the console

The code posted in GitHub prints the top 5 predictions. You should see something similar to a list of tuples, including `userId`, `accoId`, and `prediction`:

```
[('0', '75', 4.6428704512729375), ('0', '76', 4.54325166163637), ('0', '86', 4.529177571208829), ('0', '66', 4.52387350189572), ('0', '99', 4.44705391172443)]
```  
#### Display the top recommendations saved in the Database

To easily access a MySql CLI, you can use [Cloud Shell](https://cloud.google.com/shell/docs/quickstart) and type the following command line then enter your database password.

```
gcloud sql connect <YOUR_CLOUDSQL_INSTANCE_NAME>  --user=<YOUR_CLOUDSQL_USER>
```

Running the following SQL query on the database will return the predictions saved in the `Recommendation` table by `app_collaborative.py`:

```
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
