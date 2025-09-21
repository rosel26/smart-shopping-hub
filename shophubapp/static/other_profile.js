"use strict"

window.onload = is_friend;
window.setInterval(is_friend, 500);
const other_user = document.getElementById('other_username').textContent;

async function sendFriendRequest() {
    const response = await fetch(`/shophubapp/send-friend-requests/${other_user}/`)
    const results = await response.json()

    if (results.success) {
        console.log('Friend request sent successfully');
    } else {
        console.log(results.failure)
    }
    console.log('sent request');
    is_friend()
}

async function declineRequest() {
    const response = await fetch(`/shophubapp/decline-friend-requests/${other_user}/`);
    const results = await response.json()
    console.log('declined request');
    is_friend()
}

async function acceptRequest() {
    const response = await fetch(`/shophubapp/accept-friend-requests/${other_user}/`);
    const results = await response.json()
    console.log('accepted request');
    is_friend()
}

async function unfriend() {
    const response = await fetch(`/shophubapp/unfriend/${other_user}/`);
    const results = await response.json()
    console.log('Unfriend');
    is_friend()
}

async function withdraw() {
    const response = await fetch(`/shophubapp/withdraw/${other_user}/`);
    const results = await response.json()
    console.log('Unfriend');
    is_friend()
}

async function is_friend() {
    const response = await fetch(`/shophubapp/is_friend_url/${other_user}/`);
    const results = await response.json()

    let friend_div = document.getElementById('friend_div');
    friend_div.innerHTML = ''; 

    console.log(other_user)

    if (results.self) {
        return; 
    } 

    if (results.friends) {
        let li2 = document.createElement('div');
        li2.innerHTML = `<button class="btn btn-primary custom-btn" onclick="unfriend()">Unfriend</button>`;
        friend_div.appendChild(li2);
    } else if (results.sent){
        let li2 = document.createElement('div');
        li2.innerHTML = `<button class="btn btn-primary custom-btn" onclick="withdraw()">Withdraw</button>`;
        friend_div.appendChild(li2);
    } else if (results.recieved){
        let li2 = document.createElement('div');
        li2.innerHTML = `<button class="btn btn-primary custom-btn" onclick="acceptRequest()">Accept</button>`;
        friend_div.appendChild(li2);
    } else {
        let li2 = document.createElement('div');
        li2.innerHTML = `<button class="btn btn-primary custom-btn" onclick="sendFriendRequest()">Send Request</button>`;
        friend_div.appendChild(li2);
    }
    console.log('friend button refreshed');
}