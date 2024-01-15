document.addEventListener('DOMContentLoaded', function() {
    
});

function appendSuccessMessage(message) {
    warnings_div = document.querySelector('#warnings');
    message_div = document.createElement('div');
    message_div.className = 'alert alert-success alert-dismissible fade show';
    message_div.innerHTML = `
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        ${message}
    `
    warnings_div.appendChild(message_div);
}

function appendErrorMessage(message) {
    warnings_div = document.querySelector('#warnings');
    message_div = document.createElement('div');
    message_div.className = 'alert alert-danger alert-dismissible fade show';
    message_div.innerHTML = `
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        ${message}
    `
    warnings_div.appendChild(message_div);
}

function joinGroup(button) {
    const gid = button.dataset.gid;
    fetch(`/join/${gid}`)
    .then(response => {
        if (response.ok) {
            // Change button's text & function
            card_btn = document.querySelector(`#card-btn-join-${gid}`);
            card_btn.innerHTML = 'Leave';
            card_btn.dataset.bsTarget = `#leave-${gid}`;
            card_btn.setAttribute('id', `card-btn-leave-${gid}`);

            // Change capacity of group in View
            view_div = document.querySelector(`#view-${gid}`);
            let size = parseInt(view_div.querySelector(`#view-${gid}-current-size`).innerHTML, 10);
            view_div.querySelector(`#view-${gid}-current-size`).innerHTML = size + 1

            return response.json();
        } else {
            return response.json().then(error => { throw error; });
        }
    })
    .then(data => {
        // Display Successful message
        message = data.message;
        appendSuccessMessage(message);
    })
    .catch(errorMessage => {
        // Display Error message
        message = errorMessage.error;
        appendErrorMessage(message);
    });
}

function leaveGroup(button) {
    const gid = button.dataset.gid;
    fetch(`/leave/${gid}`)
    .then(response => {
        if (response.ok) {
            // Change button's text & function
            card_btn = document.querySelector(`#card-btn-leave-${gid}`);
            card_btn.innerHTML = 'Join';
            card_btn.dataset.bsTarget = `#join-${gid}`;
            card_btn.setAttribute('id', `card-btn-join-${gid}`);

            // Change capacity of group in View
            view_div = document.querySelector(`#view-${gid}`);
            let size = parseInt(view_div.querySelector(`#view-${gid}-current-size`).innerHTML, 10);
            view_div.querySelector(`#view-${gid}-current-size`).innerHTML = size - 1

            return response.json();
        } else {
            return response.json().then(error => { throw error; });
        }
    })
    .then(data => {
        // Display Successful message
        message = data.message;
        appendSuccessMessage(message);
    })
    .catch(errorMessage => {
        // Display Error message
        message = errorMessage.error;
        appendErrorMessage(message);
    })
}    

function editGroup(form) {
    const gid = form.dataset.gid;
    const csrfToken = form.querySelector("input[name='csrfmiddlewaretoken']").value;

    const name = form.querySelector('#name').value;
    const description = form.querySelector('#description').value;
    const max_size = form.querySelector('#max-size').value;
    const start = form.querySelector('#start').value;
    const end = form.querySelector('#end').value;
    fetch(`/edit/${gid}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
            name: name,
            description: description,
            max_size: max_size,
            start: start,
            end: end,
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(error => { throw error; });
        } else {
            return response.json();
        }
    })
    .then(data => {
        // Append Success Message
        appendSuccessMessage(data.message)

        // Change info of card
        group_div = document.querySelector(`#group-div-${gid}`);
        group_div.querySelector('.card-title').innerHTML = data.name;
        group_div.querySelector('.card-text').innerHTML = data.description;
        
        // Change info of modal in View
        view_div = document.querySelector(`#view-${gid}`);
        view_div.querySelector(`#view-${gid}-name`).innerHTML = data.name;
        view_div.querySelector(`#view-${gid}-description`).innerHTML = data.description;
        view_div.querySelector(`#view-${gid}-max-size`).innerHTML = data.max_size;
        view_div.querySelector(`#view-${gid}-start`).innerHTML = data.start;
        view_div.querySelector(`#view-${gid}-end`).innerHTML = data.end;
        
        // Convert time from %H:%M, %m/%d%Y format to ISO format
        var element = group_div.querySelector('.group-start-small-text');
        var formattedStart = fromIncStringToISO(data.start);
        var formattedEnd = fromIncStringToISO(data.end);
        element.dataset.start = formattedStart;
        element.dataset.end = formattedEnd;
        updateTimerAll();

        // Change info in Add to Calendar button
        var calendar_button = view_div.querySelector('add-to-calendar-button');
        calendar_button.name = data.name + " Meeting";
        calendar_button.startDate = formattedStart.substring(0, 10);
        calendar_button.endDate = formattedEnd.substring(0, 10);
        calendar_button.startTime = formattedStart.substring(11, 16);
        calendar_button.endTime = formattedEnd.substring(11, 16);
    })
    .catch(errorMessage => {
        message = errorMessage.error;
        appendErrorMessage(message);
    });
    return false;
}

function fromDateToString(date) {
    var year = date.getFullYear();
    var month = (date.getMonth() + 1).toString().padStart(2, '0');  // months are 0-indexed in JavaScript
    var day = date.getDate().toString().padStart(2, '0');
    var hours = date.getHours().toString().padStart(2, '0');
    var minutes = date.getMinutes().toString().padStart(2, '0');

    return year + '-' + month + '-' + day + 'T' + hours + ':' + minutes;
}

function fromIncStringToISO(str) {
    var parts = str.split(', ');
    var timeParts = parts[0].split(':');
    var dateParts = parts[1].split('/');

    // Create a new Date object
    var date = new Date(dateParts[2], dateParts[0] - 1, dateParts[1], timeParts[0], timeParts[1]);
    var isoString = date.toISOString().split('.')[0] + '+00:00';
    return isoString;
}

function updateTimer(element, now) {
    const startDate = new Date(element.dataset.start);
    const endDate = new Date(element.dataset.end);
    if (startDate >= now) {
        var diff = startDate - now;
        if (diff < 60000) {
            element.innerHTML = `in 1 minute`;
        } else if (diff < 3600000) {
            element.innerHTML = `in ${Math.floor(diff / 60000)} minutes`;
        } else if (diff < 7200000) {
            element.innerHTML = `in 1 hour`;
        } else if (diff < 86400000) {
            element.innerHTML = `in ${Math.floor(diff / 3600000)} hours`;
        } else if (diff < 172800000) {
            element.innerHTML = `in 1 day`;
        } else if (diff < 604800000) {
            element.innerHTML = `in ${Math.floor(diff / 86400000)} days`;
        } else if (diff < 1209600000) {
            element.innerHTML = `in 1 week`;
        } else if (diff < 2592000000) {
            element.innerHTML = `in ${Math.floor(diff / 604800000)} weeks`;
        } else if (diff < 5184000000) {
            element.innerHTML = `in 1 month`;
        } else if (diff < 31536000000) {
            element.innerHTML = `in ${Math.floor(diff / 2592000000)} months`;
        } else if (diff < 63072000000) {
            element.innerHTML = `in 1 year`;
        } else {
            element.innerHTML = `in ${Math.floor(diff / 31536000000)} years`;
        }
    } else if (now >= endDate) {
        element.innerHTML = "event over"
    } else {
        element.innerHTML = "happening";
    }
}

function updateTimerAll() {
    const now = new Date();
    document.querySelectorAll(".group-start-small-text").forEach(element => {
        updateTimer(element, now);
    });
}