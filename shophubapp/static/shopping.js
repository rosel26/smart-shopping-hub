"use strict"

// Wait for the DOM to be fully loaded before running the script
document.addEventListener("DOMContentLoaded", function() {
    const button = document.getElementById("showFormButton");
    const form = document.getElementById("productForm");

    const button2 = document.getElementById("showURLButton");
    const form2 = document.getElementById("URLForm");

    // Check if button and form exist
    if (button && form) {
        button.addEventListener("click", function() {
            console.log("Button 1 clicked");  // Debugging message
            form.style.display = form.style.display === "none" ? "block" : "none";
        });
    } 
    if (button2 && form2) {
        button2.addEventListener("click", function() {
            console.log("Button 2 clicked");  // Debugging message
            form2.style.display = form2.style.display === "none" ? "block" : "none";
        });
    } 
    else {
        console.log("Button or form not found");
    }
});

function sortProducts(products) {
    const sortElement = document.getElementById('sort');
    if (sortElement) {
        const sortOption = sortElement.value; // Get the selected sort option
        sortAndDisplayProducts(products, sortOption); // Call the sort function
    } else {
        console.log('Element with id "sort" not found');
    }
}

function getLists() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState !== 4) return
        updateLists(xhr)
    }
    xhr.open("GET", `/shophubapp/get_lists/`, true);
    xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
    xhr.send();
}

function getAllLists() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState !== 4) return
        updateLists(xhr)
    }
    xhr.open("GET", `/shophubapp/get_all_lists/`, true);
    xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
    xhr.send();
}

function displayError(message) {
    let errorElement = document.getElementById("error")
    errorElement.innerHTML = message
}

function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown"
}

function getProducts(list_id) {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState !== 4) return
        updatePage(xhr)
    }
    xhr.open("GET", `/shophubapp/get_products/${list_id}/`, true);
    xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
    xhr.send();
}

function sortAndDisplayProducts(products, sortOption) {
    // Sort the products based on the selected option
    products.sort((a, b) => {
        switch (sortOption) {
            case 'name':
                return a.name.localeCompare(b.name); // A-Z
            case '-name':
                return b.name.localeCompare(a.name); // Z-A
            case 'price':
                return a.price - b.price; // Low to High
            case '-price':
                return b.price - a.price; // High to Low
            case 'added_at':
                return new Date(a.added_at) - new Date(b.added_at); // Oldest First
            case '-added_at':
                return new Date(b.added_at) - new Date(a.added_at); // Newest First
            default:
                return 0;
        }
    });

    // Now that products are sorted, render them
    displayProducts(products);
}

function displayProducts(products) {
    const productContainer = document.getElementById('product-list-container');
    productContainer.innerHTML = "";
    let total = 0;

    for (let index = 0; index < products.length; index++) {
        const product = products[index];
        const productCard = document.createElement("div");
        productCard.classList.add("product-card");

        let store = String(product.brand)

        // Render product details
        // Handle singular vs plural "hours" left on cooldown for impulsive shopping control
        productCard.innerHTML = `
            <div class="card card-product-a">
                <img src="${product.image_url}" class="card-img-top-a" alt="Product Image">
                <div class="card-body">
                    <!-- Text container for all text content -->
                    <div class="product-text-container">
                        <h5 class="card-title product-title">${product.name}</h5>
                        <p><strong>Price:</strong> $${product.price.toFixed(2)}</p>
                        <p><strong>Brand:</strong> ${product.brand}</p>
                        ${product.is_locked
                            ? `<i class="fas fa-lock"></i>
                            <span>Link available in ${product.cooldown_hours} ${product.cooldown_hours === 1 ? 'hour' : 'hours'}</span>`
                            : `<a href="${product.product_url}" target="_blank" data-url="${product.product_url}" onclick="trackLinkClick(event)">Buy Now</a>`
                        }
                    </div>

                    <!-- Buttons -->
                    <button type="button" class="btn btn-sm delete-btn" onclick='deleteItem(${product.user.id})'>
                        x
                    </button>

                    <button type = "button" class = "btn btn-primary custom-btn btn-location" data-toggle="modal" data-target="#findLocation" onclick='initMap("${store}")'>
                        Find Location
                    </button>
                </div>
            </div>
        `;

        const col = document.createElement("div");
        col.classList.add("col-lg-3", "col-md-4", "col-sm-6", "mb-4"); // Adjust based on screen size
        col.appendChild(productCard);
        productContainer.appendChild(col);
        total += product.price;

    }

    const totalValue = document.getElementById('total');
    totalValue.innerHTML = `<h2> Total Price: $${total.toFixed(2)} </h2>`;
}

function displayLists(lists) {
    const listContainer = document.getElementById('list-container');
    listContainer.innerHTML = "";

    for (let index = 0; index < lists.length; index++) {
        const list = lists[index];
        const listCard = document.createElement("div");
        listCard.classList.add("list-card");

        // Render list details
        let div1 = `
            <div class = "card card-product">
            <img src="${list.image_url}" class="card-img-top-b" alt="Product Image">
                <div class="card-body">
                    <h5 class="card-title">
                        <a href="/shophubapp/list/${list.id}/">${list.name}</a>
                    </h5>
                    <p class="card-text"><small class="text-muted">Created on: ${list.created_at}</small></p>
                    <p class="card-text"><small class="text-muted">Made by: 
                    <a href="/shophubapp/other_profile/${list.user_id}/">${list.user} </a> </small></p>
                </div>`
        let div2 = list.is_starred? `<button type="button" class="btn btn-sm star-btn" onclick='unStarList(${list.id})'>★</button>`: 
                `<button type="button" class="btn btn-sm star-btn" onclick='starList(${list.id})'>☆</button>`

        let enddiv = `</div>`
        listCard.innerHTML = `${div1} ${div2} ${enddiv}`

        const col = document.createElement("div");
        col.classList.add("col-lg-3", "col-md-4", "col-sm-6", "mb-4"); // Adjust based on screen size
        col.appendChild(listCard);
        listContainer.appendChild(col);
    }
}


function trackLinkClick(event) {
    const url = event.target.getAttribute('data-url'); // Get the product URL from the data-url attribute
    fetch('/shophubapp/track-click/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // Ensure CSRF token is included
        },
        body: JSON.stringify({ url: url })
    }).catch((error) => console.error('Error tracking link click:', error));
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function deleteItem(id) {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return
        updatePage(xhr)
    }

    xhr.open("POST", deleteItemURL(id), true)

    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send(`csrfmiddlewaretoken=${getCSRFToken()}`)
}

function starList(id) {
    console.log(`starList called with id: ${id}`);
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return
        updatePage(xhr)
    }
    xhr.open("POST", starListURL(id), true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send(`csrfmiddlewaretoken=${getCSRFToken()}`)
    console.log("starred")
}

function unStarList(id) {
    console.log(`unstarlist called with id: ${id}`);

    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return
        updatePage(xhr)
    }
    xhr.open("POST", removeStarListURL(id), true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send(`csrfmiddlewaretoken=${getCSRFToken()}`)
    console.log("unstarred")
}

function updateLists(xhr) {
    if (xhr.status === 200) {
        let response = JSON.parse(xhr.responseText)
        displayLists(response)
        return
    }

    if (xhr.status === 0) {
        displayError("Cannot connect to server")
        return
    }

    if (xhr.getResponseHeader('content-type') && !xhr.getResponseHeader('content-type').includes('application/json')) {
        displayError(`Received status = ${xhr.status}`)
        return
    }
    console.log(xhr)
    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }
    console.log('no updating needed')
}

function updatePage(xhr) {

    console.log('updating page')
    if (xhr.status === 200) {
        try{
            let response = JSON.parse(xhr.responseText)
            sortProducts(response)
            // displayProducts(response)
            return
        } catch (e) {
            console.error('Error parsing JSON:', e);
            console.log('Received response:', xhr.responseText);
        }
    }

    if (xhr.status === 0) {
        displayError("Cannot connect to server")
        return
    }

    if (!xhr.getResponseHeader('content-type') === 'application/json') {
        displayError(`Received status = ${xhr.status}`)
        return
    }
    console.log(xhr)
    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }
    console.log('no updating needed')
}

// Attach the event listener to the buttons for each notification
document.querySelectorAll('.accept-btn').forEach(button => {
    button.addEventListener('click', function(event) {
        const notificationId = event.target.getAttribute('data-id'); // Get the notification ID
        acceptCollaboration(event, notificationId);  // Call the function with the notification ID
    });
});

function declineCollaboration(notificationId) {
    $.ajax({
        url: `/shophubapp/decline_collaboration/${notificationId}/`,
        method: 'POST',
        data: {
            csrfmiddlewaretoken: '{{ csrf_token }}',
        },
        success: function(response) {
            if (response.status === 'success') {
                // Remove the notification from the UI
                $(`#notification-${notificationId}`).remove();
            } else {
                alert('An error occurred while declining the collaboration.');
            }
        },
        error: function(error) {
            alert('An error occurred while declining the collaboration.');
        }
    });
}


// Note: This example requires that you consent to location sharing when
// prompted by your browser. If you see the error "The Geolocation service
// failed.", it means you probably did not give permission for the browser to
// locate you.
let map, infoWindow, directionsService, directionsRenderer;


async function initMap(store) {
    const { Map } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    const directionsService = new google.maps.DirectionsService();
    const directionsRenderer = new google.maps.DirectionsRenderer();

    // Try HTML5 geolocation.
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
          map = new Map(document.getElementById('map'), {
            center: pos,
            zoom: 10,
            mapId: "DEMO_MAP_ID",
        });

        directionsRenderer.setMap(map);

        const contentString = `
            <div>
            <h3>Your Location</h3>
            <p>${pos.formatted_address}</p>
            </div>
        `;

        infoWindow = new google.maps.InfoWindow({content: contentString});

        const marker = new AdvancedMarkerElement({
            map: map,
            position: pos,
            title: "Your Location",
        });

        marker.addListener("click", () => {
            console.log("Marker clicked!");
            infoWindow.open(map, marker);
        });
        
        const request = {
            query: String(store),
            fields: ["name", "geometry", "formatted_address"],
          };

          let service = new google.maps.places.PlacesService(map);
          let locationInfo = document.getElementById('location-info')

          service.textSearch(request, (results, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK && results) {
                const storeResult = results.find(result => result.name.toLowerCase().includes(store.toLowerCase()));
                if (storeResult) {
                    const end = {
                        lat: storeResult.geometry.location.lat(),
                        lng: storeResult.geometry.location.lng(),
                    };
                
                    const storeMarker = new AdvancedMarkerElement({
                        map: map,
                        position: end,
                        title: storeResult.name,
                    });
                    
                    map.setCenter(storeResult.geometry.location);
     
                    calcRoute(directionsService, directionsRenderer, pos, end, storeResult, storeMarker, map);
                }
                else {
                    locationInfo.innerHTML = `
                        <h3>${store} is not within 50 miles</h3>
                    `
                }
        
            }
          });
        },
        () => {
          handleLocationError(true, infoWindow, map.getCenter());
        },
      );
    } else {
      // Browser doesn't support Geolocation
      handleLocationError(false, infoWindow, map.getCenter());
    }
}

function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(
    browserHasGeolocation
      ? "Error: The Geolocation service failed."
      : "Error: Your browser doesn't support geolocation.",
  );
  infoWindow.open(map);
}


function calcRoute(directionsService, directionsRenderer, start, end, info, storeMarker, map) {
    var request = {
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.DRIVING
    };

    directionsService.route(request, function(response, status) {
      if (status == 'OK') {
        directionsRenderer.setDirections(response);

        const duration = response.routes[0].legs[0].duration.text;
        const distance = response.routes[0].legs[0].distance.text;

        let locationInfo = document.getElementById('location-info')

        if ((response.routes[0].legs[0].distance.value / 1609) > 50) {
            locationInfo.innerHTML = `
                <h3>${info.name} is not within 50 miles</h3>
                <p><strong>Address:</strong> ${info.formatted_address}</p>
                <p><strong>Distance:</strong> ${distance}</p>
                <p><strong>Driving Time:</strong> ${duration}</p>
            `
        }
        else {
            locationInfo.innerHTML = `
                <h3>${info.name}</h3>
                <p><strong>Address:</strong> ${info.formatted_address}</p>
                <p><strong>Distance:</strong> ${distance}</p>
                <p><strong>Driving Time:</strong> ${duration}</p>
            `;
        }
        
      } else {
        console.error("Directions request failed due to " + status);
      }
    });
  }

// restricted page functions

function displayProductsRestrict(products) {
    const productContainer = document.getElementById('product-list-container');
    productContainer.innerHTML = "";
    console.log('all products: ', products);
    let total = 0;

    for (let index = 0; index < products.length; index++) {
        const product = products[index];
        const productCard = document.createElement("div");
        productCard.classList.add("product-card");
        console.log(index)
        console.log(product)

        // Render product details
        productCard.innerHTML = `
            <div class = "card">
                <img src="${product.image_url}" class="card-img-top" id="product-img-top" alt="Product Image" style="width: 150px; height: auto; max-height: 150px; object-fit: cover;>
                <div class="card-body" id="product-body">
                    <h5 class="card-title" id="product-title">
                        <a href="${product.product_url}" class="product-link">${product.name}</a>
                    </h5>
                    <p id="product-brand"><strong>Price:</strong> $${product.price}</p>
                    <p id="product-price"><strong>Brand:</strong> ${product.brand}</p>
                </div>
            </div>
        `;

        const col = document.createElement("div");
        col.classList.add("col-lg-3", "col-md-4", "col-sm-6", "mb-4"); // Adjust based on screen size
        col.appendChild(productCard);
        productContainer.appendChild(col);
        total += product.price;

    }

    const totalValue = document.getElementById('total');
    totalValue.innerHTML = `<h2> Total Price: $${total.toFixed(2)} </h2>`;
}

function getProductsRestrict(list_id) {
    if (typeof list_id === "undefined" || list_id === null) {
        console.error("Error: list_id is undefined or null.");
        throw new Error("The 'list_id' parameter is required but is undefined or null.");
    }
    console.log('getting products')
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState !== 4) return
        updatePageRestrict(xhr)
    }
    xhr.open("POST", `/shophubapp/get_products/${list_id}/`, true);
    xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
    xhr.send();
}

function updatePageRestrict(xhr) {
    console.log('updating page')
    if (xhr.status === 200) {
        let response = JSON.parse(xhr.responseText)
        displayProductsRestrict(response)
        return
    }

    if (xhr.status === 0) {
        displayError("Cannot connect to server")
        return
    }


    if (!xhr.getResponseHeader('content-type') === 'application/json') {
        displayError(`Received status = ${xhr.status}`)
        return
    }
    console.log(xhr)
    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }
    console.log('no updating needed')
}

function getListsRestrict(list_id) {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState !== 4) return
        updatePageRestrict(xhr)
    }

    xhr.open("GET", `/shophubapp/get_products/${list_id}`, true);
    xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
    xhr.send();
}

function requestSent() {
    let reqButton = document.getElementById("divRequestButton")
    reqButton.innerHTML = `
        <button id="requestButton" type="button" class="btn btn-secondary custom-btn" disabled>Request to Collaborate Sent</button>
    `
}

function accClick() {
    let accButton = document.getElementById("acceptButton")
    accButton.innerHTML = `
        <button type="button" class="btn btn-success btn-sm" disabled>Accepted</button>
    `
    let rejButton = document.getElementById("rejectButton")
    rejButton.innerHTML = `
        <button type="button" style="display: none;" disabled></button>
    `
}

function rejClick() {
    let accButton = document.getElementById("acceptButton")
    accButton.innerHTML = `
        <button type="button" style="display: none;" disabled></button>
    `
    let rejButton = document.getElementById("rejectButton")
    rejButton.innerHTML = `
        <button type="button" class="btn btn-danger btn-sm" disabled>Rejected</button>
    `
}

document.addEventListener("DOMContentLoaded", function() {
    const searchBar = document.getElementById('search-bar');
    const resultsContainer = document.getElementById('autocomplete-results');

    if (searchBar) {
        console.log('Search bar is found');
    } else {
        console.log('Search bar not found!');
        return
    }
    searchBar.addEventListener("input", function() {
        const query = searchBar.value.trim();
        fetchResults(query);
        console.log('User typed:', query);
    });

    async function fetchResults(query) {
        console.log('Fetching usernames', query);
        const response = await fetch(`/shophubapp/search-profiles/?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        console.log('Fetched');
        displayResults(data);
    }
    async function displayResults(data){
        resultsContainer.innerHTML = ''; 
        if (Array.isArray(data.results) && data.results.length > 0 || (Array.isArray(data.lists) && data.lists.length > 0)) {
            
            data.results.forEach((result) => {
                let div = document.createElement('div');
                let other = `<a href="/shophubapp/other_profile/${result.user_id}/"> ${result.username} </a>`
                let closediv = `</div>`
                div.innerHTML = `${other} ${closediv}`
                resultsContainer.appendChild(div);
            })
            data.lists.forEach((list) => {
                let div = document.createElement('div');
                let other_list = `<a href="/shophubapp/list/${list.list_id}/">${list.name}</a>`
                let closediv = `</div>`
                div.innerHTML = `${other_list} ${closediv}`
                resultsContainer.appendChild(div);
            })
        } 
        else {
            resultsContainer.innerHTML = '<div>No results found</div>';
        }
    };
});

async function renderFriendsList() {
    const friendsListElement = document.getElementById('friendsList');

    if (friendsListElement) {
        console.log('friendsList found');
    } else {
        console.log('friendsList not found');
        return
    }

    const response = await fetch(`/shophubapp/get-friend-list/`);
    const results = await response.json()

    friendsListElement.innerHTML = ''; 
    
    results.friend_requests.forEach(friend => {
        let div = document.createElement('div');
        let other = `<a href="/shophubapp/other_profile/${friend.user_id}/"> ${friend.username} </a>`
        let closediv = `</div>`
        div.innerHTML = `${other} ${closediv}`
        friendsListElement.appendChild(div);
    });

    const noUsersMessage = document.getElementById('noFriendsMessage');

    if (friendsListElement.children.length > 0) {
        friendsListElement.style.display = "block";
        noUsersMessage.style.display = 'none';
    } else {
        noUsersMessage.style.display = 'block'; 
        friendsListElement.style.display = 'none';
    }
}

async function renderRequests() {
    const response = await fetch(`/shophubapp/get-friend-requests/`);
    const results = await response.json()
        
    let requestsList = document.getElementById('friendRequestList');
    requestsList.innerHTML = ''; 

    results.friend_requests.forEach(request => {
        let li = document.createElement('div');
        li.className = "list-group-item d-flex justify-content-between align-items-center";
        li.innerHTML = `
            <span>${request}</span>
            <div>
                <button class="btn btn-success btn-sm me-2" onclick="acceptRequest('${encodeURIComponent(request)}')">Accept</button>
                <button class="btn btn-danger btn-sm" onclick="declineRequest('${encodeURIComponent(request)}')">Decline</button>
            </div>
                    `;
        requestsList.appendChild(li);
    });
    console.log('rendered requests');
}

async function declineRequest(request) {
    const response = await fetch(`/shophubapp/decline-friend-requests/${encodeURIComponent(request)}/`);
    const results = await response.json()
    console.log('declined request');
    renderRequests()
}

async function acceptRequest(request) {
    console.log(encodeURIComponent(request))
    const response = await fetch(`/shophubapp/accept-friend-requests/${encodeURIComponent(request)}/`);
    const results = await response.json()
    console.log('accepted request');
    renderRequests()
}

