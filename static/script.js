// ==========================================
// AI QUIZ
// ==========================================

let quizQuestions = [];
let currentQuestion = 0;
let score = 0;
let selectedAnswer = null;


// ==========================================
// GENERATE QUIZ
// ==========================================

async function generateQuiz() {

    const topic = document.getElementById("topic").value;
    const difficulty = document.getElementById("difficulty").value;
    const number = document.getElementById("number").value;

    if (!topic) {
        alert("Please enter a topic.");
        return;
    }

    const quizArea = document.getElementById("quiz-area");

    quizArea.innerHTML = `
        <div class="loading">
            🤖 AI is creating your quiz...
        </div>
    `;

    try {

        const response = await fetch("/generate_quiz", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                topic: topic,
                difficulty: difficulty,
                number: number
            })

        });

        const data = await response.json();

        if (!data.success) {

            quizArea.innerHTML = `
                <div class="error-box">
                    ❌ ${data.message}
                </div>
            `;

            return;
        }

        quizQuestions = data.questions;

        currentQuestion = 0;
        score = 0;
        selectedAnswer = null;

        showQuestion();

    }

    catch (error) {

        quizArea.innerHTML = `
            <div class="error-box">
                ❌ Something went wrong.
                Please try again.
            </div>
        `;

    }
}


// ==========================================
// SHOW QUESTION
// ==========================================

function showQuestion() {

    const quizArea = document.getElementById("quiz-area");

    if (currentQuestion >= quizQuestions.length) {

        finishQuiz();

        return;
    }

    const question = quizQuestions[currentQuestion];

    selectedAnswer = null;

    let optionsHTML = "";

    question.options.forEach((option, index) => {

        optionsHTML += `
            <button
                class="option-button"
                onclick="selectOption(this, ${index})">

                ${String.fromCharCode(65 + index)}.
                ${option}

            </button>
        `;

    });


    quizArea.innerHTML = `

        <div class="quiz-box">

            <div class="quiz-top">

                <span>
                    Question
                    ${currentQuestion + 1}
                    /
                    ${quizQuestions.length}
                </span>

                <span>
                    Score: ${score}
                </span>

            </div>


            <div class="progress-container">

                <div
                    class="progress-bar"
                    style="width:
                    ${
                        ((currentQuestion + 1) /
                        quizQuestions.length) * 100
                    }%;">
                </div>

            </div>


            <h2>
                ${question.question}
            </h2>


            <div class="options">

                ${optionsHTML}

            </div>


            <button
                id="check-button"
                onclick="checkAnswer()"
                class="primary-button full">

                Check Answer

            </button>


            <div id="answer-result"></div>

        </div>

    `;
}


// ==========================================
// SELECT OPTION
// ==========================================

function selectOption(button, index) {

    document
        .querySelectorAll(".option-button")
        .forEach(btn => {

            btn.classList.remove("selected");

        });

    button.classList.add("selected");

    selectedAnswer = index;
}


// ==========================================
// CHECK ANSWER
// ==========================================

function checkAnswer() {

    if (selectedAnswer === null) {

        alert("Please select an answer first.");

        return;
    }

    const question = quizQuestions[currentQuestion];

    const result =
        document.getElementById("answer-result");

    const buttons =
        document.querySelectorAll(".option-button");


    // Find correct answer index

    const correctIndex =
        question.options.findIndex(
            option =>
                option.trim() ===
                question.answer.trim()
        );


    // Highlight correct answer

    if (correctIndex !== -1) {

        buttons[correctIndex]
            .classList.add("correct");

    }


    if (selectedAnswer === correctIndex) {

        score++;

        result.innerHTML = `

            <div class="correct-box">

                🎉 Correct!

                <p>
                    ${question.explanation}
                </p>

            </div>

        `;

    }

    else {

        result.innerHTML = `

            <div class="wrong-box">

                ❌ Wrong Answer

                <p>

                    <strong>
                        Correct answer:
                    </strong>

                    ${question.answer}

                </p>

                <p>
                    ${question.explanation}
                </p>

            </div>

        `;

    }


    document.getElementById(
        "check-button"
    ).style.display = "none";


    const nextButton =
        document.createElement("button");


    nextButton.className =
        "primary-button full";


    if (
        currentQuestion ===
        quizQuestions.length - 1
    ) {

        nextButton.innerText =
            "Finish Quiz";

    }

    else {

        nextButton.innerText =
            "Next Question →";

    }


    nextButton.onclick = function () {

        currentQuestion++;

        showQuestion();

    };


    document
        .getElementById("quiz-area")
        .querySelector(".quiz-box")
        .appendChild(nextButton);
}


// ==========================================
// FINISH QUIZ
// ==========================================

async function finishQuiz() {

    const quizArea =
        document.getElementById("quiz-area");

    const total =
        quizQuestions.length;

    const percentage =
        Math.round((score / total) * 100);


    quizArea.innerHTML = `

        <div class="result-box big-result">

            <div class="result-emoji">
                🏆
            </div>

            <h1>
                Quiz Completed!
            </h1>

            <p>
                You scored
            </p>

            <h2>
                ${score}/${total}
            </h2>

            <h3>
                ${percentage}%
            </h3>

            <p>

                ${
                    percentage >= 80
                    ? "🔥 Excellent work!"
                    : percentage >= 60
                    ? "👏 Good job!"
                    : "💪 Keep practicing!"
                }

            </p>

            <button
                onclick="location.reload()"
                class="primary-button">

                🔄 New Quiz

            </button>

        </div>

    `;


    const topic =
        document.getElementById("topic").value;


    await fetch("/save_quiz", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            topic: topic,
            score: score,
            total: total

        })

    });

}


// ==========================================
// NUMBER GUESSING GAME
// ==========================================

async function makeGuess() {

    const input =
        document.getElementById("guess");

    const guess =
        input.value;


    if (!guess) {

        alert("Enter a number first.");

        return;
    }


    const response =
        await fetch("/game/guess", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                guess: guess
            })

        });


    const data =
        await response.json();


    document.getElementById(
        "game-message"
    ).innerText = data.message;


    input.value = "";

}