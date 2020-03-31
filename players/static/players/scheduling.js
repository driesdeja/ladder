const schedulable_matches = document.querySelectorAll('.schedulable-match');
const time_slots = document.querySelectorAll('.match-time-slot');
const list_of_matches = document.getElementById('matches');


let draggedMatch = null;


for (let i = 0; i < schedulable_matches.length; i++) {
    const item = schedulable_matches[i];

    item.addEventListener('dragstart', function () {
        draggedMatch = item;
        setTimeout(function () {
            item.style.display = 'none';
        }, 0)
    });

    item.addEventListener('dragend', function () {
        setTimeout(function () {
            draggedMatch.style.display = 'block';
            draggedMatch = null;
        }, 0);
    });

    for (let j = 0; j < time_slots.length; j++) {
        const slot = time_slots[j];

        slot.addEventListener('dragover', function (e) {
            e.preventDefault();
        });

        slot.addEventListener('dragenter', function (e) {
            e.preventDefault();
            this.style.backgroundColor = 'rgba(0,0,0,0.2)';
        });

        slot.addEventListener('dragleave', function () {
            this.style.backgroundColor = 'rgba(0,0,0,0.1)';
        });

        slot.addEventListener('dragstart', function () {
            slot.addEventListener('drop', handleDrop);
        })

        slot.addEventListener('drop', handleDrop);

    }

}
list_of_matches.addEventListener('dragenter', function (e) {
    e.preventDefault();
    this.style.backgroundColor = 'rgba(0,0,0,0.8)';
});

list_of_matches.addEventListener('dragover', function (e) {
    e.preventDefault();
    this.style.backgroundColor = 'rgba(0,0,0,0.8)';
});

list_of_matches.addEventListener('dragleave', function () {
    this.style.backgroundColor = 'rgba(0, 0, 0, 0.1)';
});

list_of_matches.addEventListener('drop', function (e) {
    draggedMatch.style.borderStyle = 'dashed';
    this.insertBefore(draggedMatch, list_of_matches.firstChild);
    this.style.backgroundColor = 'rgba(0,0,0,0.1)';


});

function handleDrop(e) {
    e.preventDefault();
    this.append(draggedMatch);
    this.style.backgroundColor = 'rgba(0,0,0,0.1)';
    this.removeEventListener('drop', handleDrop);

}

function saveMatches() {
    const matches = [];
    console.log('saving matches');
    //get all the time elements
    let timeElements = document.querySelectorAll('.time-slot');
    for (let i = 0; i < timeElements.length; i++) {
        let time = timeElements[i].querySelector('.match-time').firstElementChild.getAttribute('value');
        let schedulableMatches = timeElements[i].querySelectorAll('.schedulable-match');
        for (let k = 0; k < schedulableMatches.length; k++) {
            console.log('schedulableMatch :' + schedulableMatches[k])
            let inputs = schedulableMatches[k].getElementsByTagName('input');
            for (let j = 0; j < inputs.length; j++) {
                console.log('input: ' + inputs[j].value);
                let match = {
                    'timeslot': time.trim(),
                    'match': inputs[j].value
                }
                matches.push(match);
            }
        }
    }

    const scheduledMatches = document.getElementById('scheduled-matches');
    scheduledMatches.setAttribute('value', JSON.stringify(matches));
    document.getElementById('match-schedule-form').submit();
    console.log(matches);
}