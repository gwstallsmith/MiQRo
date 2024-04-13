


// JavaScript for modal functionality
document.addEventListener("DOMContentLoaded", function() {

    // Get the modal
    var modal = document.getElementById('chooseGroupModal');
  
    // Get the buttons
    var fetchButton = document.getElementById("fetchButton");
    var createButton = document.getElementById("createButton");
    var startScanButton = document.getElementById("startScanButton");
  
    // When the user clicks the button, open the modal
    fetchButton.onclick = function() {
        modal.style.display = "block";
        fetchButton.classList.add('active');
        createButton.classList.remove('active');
    }
  
    createButton.onclick = function() {
        modal.style.display = "block";
        createButton.classList.add('active');
        fetchButton.classList.remove('active');
    }
  
    // form ID - group form
    var form = modal.querySelector('#grp-form');


    // Fetch labs data from the backend
    // Replace this with actual AJAX call to fetch labs data
    // Here, I'm simulating the labs data
    const labsData = [
        { id: 1, name: 'Lab 1' },
        { id: 2, name: 'Lab 2' },
        { id: 3, name: 'Lab 3' }
    ];
    const grpData = [
        { id: 1, name: 'Group 1' },
        { id: 2, name: 'Group 2' },
        { id: 3, name: 'Group 3' }
    ];
  
  
    // Function to dynamically populate the lab select menu
    function populateLabSelect(labsData) {
        labsData.forEach(lab => {
            const option = document.createElement('option');
            option.value = lab.id; // Assuming lab has an id property
            option.textContent = lab.name; // Assuming lab has a name property
            labSelect.appendChild(option);
        });
    }

    function populateGrpSelect(grpData) {
        grpData.forEach(grp => {
            const option = document.createElement('option');
            option.value = grp.id; // Assuming lab has an id property
            option.textContent = grp.name; // Assuming lab has a name property
            grpSelect.appendChild(option);
        });
    }
  

    const labSelect = document.getElementById("labSelect");
    const grpSelect = document.getElementById("grpSelect");
    populateLabSelect(labsData);
    populateGrpSelect(grpData);

    
    // Handle form submission
    form.addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent form submission
        // You can add your form submission logic here
    });

  
    // Set up event listener for startScanButton - THIS IS WHAT SENDS TO RIGHT PAGE!
    startScanButton.onclick = function() {
  
        // Serialize form data into an object
        const formData = {};
        new FormData(form).forEach((value, key) => {
            formData[key] = value;
        });

   
        // Iterate over labsData array, labSelect.value is // LAB ID number
        for (const lab of labsData) {
            if (labSelect.value == lab.id) {
                sessionStorage.setItem("labValue", lab.name);
                break;
            }
        }

        // Iterate over labsData array, labSelect.value is // LAB ID number
        for (const grp of grpData) {
            if (grpSelect.value == grp.id) {
                sessionStorage.setItem("grpValue", grp.name);
                break;
            }
        }
       
        // This is a test 
        // sessionStorage.setItem("test", "Here I am");
       
        
        // Close the modal after form submission
        $('#chooseGroupModal').modal('hide');
  
        // Redirect to different pages based on the action type after a short delay to allow the modal to close
        setTimeout(function() {

            if (fetchButton.classList.contains('active')) {
                window.location.href = "file:///home/omo776/scan_fetch_page";
            } else if (createButton.classList.contains('active')) {
                window.location.href = "file:///home/omo776/scan_create_page";
            }

        }, 500); // Adjust the delay time as needed
       
    };


    
  
    // Open the modal when necessary
    function openModal() {
        $('#chooseGroupModal').modal('show');
    }
  
    // Example: Open the modal when clicking on a button with id="openModalButton"
    var openModalButton = document.getElementById("openModalButton");
    if (openModalButton) {
        openModalButton.addEventListener("click", openModal);
    }

  
  
    
  });
  
  