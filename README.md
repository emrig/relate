# Relate - Find out who's in your documents

<div align="center">
  <img src="https://github.com/emrig/relate/blob/master/static/images/Dashboard.png"><br>
</div>

Relate is a document analysis tool designed for journalists. The goal of Relate is to lift the burden of manually identifying the who and where within a document set through Named Entity Extraction (NER), focusing solely on identifying the people, organizations, and locations within a collection of documents, also known as the corpus. Relationships between these entities are recorded by identifying the documents they appear in together then arranged for the user to navigate through in a simple user interface.

**Install instructions**


Relate first requires Docker to be installed in order to run the software in isolated virtual containers which allow the user to run the application with little initial setup. The free ‘Developer’ version can be downloaded from the Docker website for both Mac and Windows operating systems from the [product website](https://www.docker.com/products/docker-desktop).
Once installed, you should see the docker symbol in the task or menu bar of your operating system. Open the settings window, click on ‘Advanced’ and ensure you have these minimum requirements set:

* CPUs: 2
* Memory: 2048 MB
* Disk Image Size: 10 GB


After Docker is installed and running, 

Download Relate and unzip the files to the preferred location in your file system. 
Place the files you would like to add to Relate in the /relate/documents/ folder. Relate will read any file or folder in this directory. 
Open a Terminal window (Mac) or Command Prompt (Windows) and change the working directory to the Relate directory by typing the cd command followed by the full path of the Relate folder.
		<br><br>`(Windows)  c:\> cd c:\relate\`<br><br>
Ensure the directory has the docker-compose.yml and dockerfile files, they contain the Docker instructions to build and deploy the application. Then, execute the following command to install the application. You will need to execute this command every time you would like to start Relate.
  <br><br>`c:\relate> docker-compose up`<br><br>
The initial setup will take a few minutes because it needs to download the necessary software components for the application to run. Your computer will need internet access for this step.
Relate is successfully running when it begins to process the documents in the /relate/documents/ folder. Your command window will look something like this:
<br><br>
`Found 517401 document`<br>
`worker_1   | Extracting entities from documents..`<br>
`worker_1   | Parsing Docs`<br>
`worker_1   | Files left:  517401 `<br>
`worker_1   | Batch size  500 Time:  0:00:39.835696`<br>
`worker_1   | Total time:  0:00:39.97562`<br>
`worker_1   | Files left:  516901 `<br>


**Note**: Depending on the number of documents in the user’s directory, the processing stage could take a long time, up to several hours if there are hundreds of thousands of documents to read through. However, the extraction engine will run in the background so the user can use the application during this time.
