let currentWordIndex = 0;
let totalWords = 0;

updateProgressBar(0);
document.addEventListener('DOMContentLoaded', function() {
    totalWords = document.getElementById('total-words').value;
});

document.getElementById('typing-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const userInput = document.getElementById('user-input').value;
    const correctTranslation = document.getElementById('correct-translation').value;
    const submitButton = document.getElementById('submit-button');
    const action = submitButton.dataset.action;

    if (action === 'check') {
        fetch('/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'user_input': userInput,
                'correct_translation': correctTranslation
            })
        })
        .then(response => response.json())
        .then(data => {
            const resultElement = document.getElementById('result');
            const errorCountElement = document.getElementById('error-count');
            if (userInput === correctTranslation) {
                resultElement.textContent = 'Правильно';
                resultElement.className = 'correct';
            } else {
                resultElement.textContent = 'Неправильно, правильна відповідь: ' + correctTranslation;
                resultElement.className = 'incorrect';
            }
            errorCountElement.textContent = data.error_count;
            document.getElementById('user-input').disabled = true;
            currentWordIndex++;
            if (data.game_over) {
                submitButton.textContent = submitButton.dataset.checkResultsText;
                submitButton.dataset.action = 'check-results';
                submitButton.dataset.redirectUrl = '/results';
            } else {
                submitButton.textContent = submitButton.dataset.continueText;
                submitButton.dataset.action = 'continue';
                submitButton.dataset.nextWord = data.next_word;
                submitButton.dataset.nextTranslation = data.next_translation;
            }
            updateProgressBar((currentWordIndex / totalWords) * 100);
        });
    } else if (action === 'continue') {
        const nextWord = submitButton.dataset.nextWord;
        const nextTranslation = submitButton.dataset.nextTranslation;
        document.getElementById('main-second-text').textContent = nextWord;
        document.getElementById('correct-translation').value = nextTranslation;
        document.getElementById('user-input').value = '';
        document.getElementById('user-input').disabled = false;
        document.getElementById('result').textContent = '';
        submitButton.textContent = submitButton.dataset.checkText;
        submitButton.dataset.action = 'check';
        document.getElementById('user-input').focus();
    } else if (action === 'check-results') {
        window.location.href = submitButton.dataset.redirectUrl;
    }
});

document.getElementById('restart-button').addEventListener('click', function() {
    location.reload();
});

function updateProgressBar(progress) {
    const progressBar = document.querySelector('.progress-bar');
    progressBar.style.width = progress + '%';
    progressBar.parentElement.setAttribute('aria-valuenow', progress);
}
