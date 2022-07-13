# Fog Computing Prototyping Assignment: Smart Hospital Features
Hello, this is our Prototyping assignment, where we implemented a face sensor and a simulated air quality control sensor to improve conditions within the hospital and ensure that one is wearing a mask when entering
## Setup
Our project includes four clients, which are all in charge of seperate things. These all communicate with one cloud system, which handles certain responsibilities.
### Clients
#### Face sensor
The job of the face sensor is to check whether or not a person standing in front of it is wearing a mask. For this, we trained a Tensorflow model with a small set of data to check if a person is wearing a mask. This then checks the camera feed, and uses its model to return a confidence score of its sureness that the person is or isn't wearing a mask. This score is then sent to the cloud. Also, to prevent overloading the cloud with excess data, we do not constantly exchange data with the cloud but rather send the data a time per 2 seconds. This time could be manually manipulated according to the users need.
#### Air quality
Our air quality sensor  detects the parts per million of carbon dioxide in the air of the hospital and sends it to the cloud. This is just a purely simulated sensor though, so in order to test our setup we have it increase by  a random value between 10 and 20 every second while air conditioning is turned off, or decrease by 10 if it is on.
#### Door opener
The door opener is a sensor that receives input from the cloud. From there, it gets the information of whether or not it should open the door and keep it open for three seconds in order to let a person pass through. 
#### Air conditioning
The air conditioner also gets information from the cloud and is responsible for turning the air conditioning on and off in order to improve the existing air quality. It receives this input from the cloud, which makes its decision based on data given by the air quality sensor. 
### Cloud
The cloud is responsible for different things depending on the sensor/client it is communicating with. 
For the face sensor, it receives the confidence score and communicates the decision to open or close the door to the door opener. 
The air quality sensor sends its data to the cloud, where the cloud then decides whether or not to turn the air conditioner on or off depending on the value it has received. The cloud sends data to the door opener, which the opener then uses to keep a door open or shut.Lastly, the air conditioner receives on/off signals from the cloud to help regulate the air quality and save electricity in the case that the air conditioner can be turned off.
## Documentation
The PDF explaining our project can be found in the documentation folder, along with the video. There we also go into detail how we handle reliable messenging
## Sources 
Sources for the video are in the sources folder

