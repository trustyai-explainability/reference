# TrustyAI Database Connection

# Deploying a MariaDB
There are two options for installing Maria: either we create a db-credentials secret _first_, which
determines the database password, username, etc., or instead we let the MariaDB operator create
passwords for us.

## Option 1: Creating credentials secret before deploying the DB
### Create Secret
In your model namespace:

`oc apply -f db-credentials-secret.yaml`

### Maria Installation 
1) Install the MariaDB Operator
2) In the MariaDB Operator Page:
   1) From the MariaDbOperators page, create a default MariadbOperator
   2) From the MariaDbOperators page, create a MariaDB. Use the example [mariadb-with-db-credentials.yaml](mariadb-with-db-credentials.yaml) for reference on how to populate the form.

You should now see four pods spin up in your namespace: `mariadb-0`, `mariadb-1`, `mariadb-2`, and `mariadb-metrics-xyz`

## Option 2: Creating credentials secret after deploying the DB

### Maria 
1) Install the MariaDB Operator
2) In the MariaDB Operator Page:
   1) From the MariaDbOperators page, create a default MariadbOperator
   2) From the MariaDbOperators page, create a default MariaDB.
      1) Observe the default values for the following fields:
         * `database` 
         * `username`

### Create the db-credentials secret
1) Navigate to Workloads -> Secrets in the Openshift console
2) Open the `mariadb-password` secret
3) Note down the value of `password` within the secret (click "Reveal Values")
4) Filling out the values of `database`, `username`, and `password` noted earlier in the template below, create the following secret in your model namespace:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  databaseKind: mariadb
  databaseUsername: $username
  databasePassword: $password
  databaseService: mariadb-service
  databasePort: '3306'
  databaseName: $database
 ```

# Deploying TrustyAI:
`oc apply -f trustyai-cr.yaml`

Notice in the CR, we refer to the `db-credentials` secret we created earlier:
```yaml
apiVersion: trustyai.opendatahub.io/v1alpha1
kind: TrustyAIService
metadata:
  name: trustyai-service
spec:
  storage:
    format: "DATABASE"
    size: "1Gi"
    databaseConfigurations: db-credentials
  metrics:
    schedule: "5s"
```

# Debugging
If the Maria pods are crashing at deployment, try:
1) Delete the MariaDB instance
2) Delete all PersistentVolumes that are bound to a MariaDB PVC
3) Recreate the MariaDB instance

This is caused by the new Maria deployment attempting to connect to the storage that may be left
behind by a previous MariaDB instance. Cleaning up the PVCs should rectify this. 