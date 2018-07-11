# Scrips Description and Usage Methods  

### Script to Execute a Command In All Hosts  

* **Description:** The script receive a command as parameter and execute it in the hosts managed by the RCBTM - using the DNS names registered in the server.  

* **Location:** [execute_all_hosts](https://github.com/futebol-ufmg/RCBTM/blob/master/scripts/execute_all_hosts.sh)  

* **Usage:**  

```  
./execute_all_hosts.sh [command]  
```  

### Script to Execute a Command In All Raspberries PI   

* **Description:** The script receive a command as parameter and execute it in the raspberries PI managed by the RCBTM - using the DNS names registered in the server.  

* **Location:** [execute_all_rasps](https://github.com/futebol-ufmg/RCBTM/blob/master/scripts/execute_all_rasps.sh)  

* **Usage:**  

```  
./execute_all_rasps.sh [command]  
```  

### Dependencies Installation Script  

* **Description:** The script installs the dependencies necessary to run CBTM, including libvirt, gnuradio and python. Warning: this script requires suepr user privileges so you may be prompted for the password.

* **Location:** [install](https://github.com/futebol-ufmg/RCBTM/blob/master/scripts/install.sh)  

* **Usage:**  

```  
./install.sh  
```  

### Environment Cleanup Script  

* **Description:** The script cleans up the environment for the dependencies installation process. It removes previous installations of libvirt that might conflict with the version used by CBTM. Warning: this script requires suepr user privileges so you may be prompted for the password.

* **Location:** [pre-clean](https://github.com/futebol-ufmg/RCBTM/blob/master/scripts/pre-clean.sh)  

* **Usage:**  

```  
./pre-clean.sh  
```  

### Testing Script  

* **Description:** The script tests if libvirt is installed and running.

* **Location:** [test](https://github.com/futebol-ufmg/RCBTM/blob/master/scripts/test.sh)  

* **Usage:**  

```  
./test.sh  
```  

<!---

*In Construction*

### Prerequisites

In order to execute the RCBTM, the following softwares are needed: 

```
apt-get install python (version)
In Construction
```

### Installing

```
In Construction
```

## Running the tests

```
In Construction
```

## Deployment

In Construction

## Built With

* [In Construction](site: In Construction) - In Construction

## Contributing

In Construction

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

In Construction

-->
