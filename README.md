# Deployment
 1. Open the elastic beanstalk console
 2. Click `Create a new environment` and select `Worker environment`
 3. Enter `Application name` and `Environment name`
 4. `Platform` is python, and `Platform branch` is python 3.8
 5. Upload the zip file of the code and click `Configure more options`
 6. Click `Instance and` select `EC2-Security-Group`
 7. Click `Capacity`, select the `load balanced` option with max 3 instances, and select `Instance type` with `t2.medium`
 8. Click `Worker` and customize the SQS queue for the worker
 9. Click `Security`, add your key pair `"cloudprog"` to the instances, and choose `"EC2Role"` (must have write permission for CloudWatch)
 10. Click `Create Envrionment`