document.addEventListener("DOMContentLoaded", () => {
    const game = document.body.dataset.game;
    const stage = document.getElementById("game-stage");
    const startPanel = document.getElementById("start-panel");
    const startButton = document.getElementById("start-game");
    const finishButton = document.getElementById("finish-game");
    const scoreNode = document.getElementById("score");
    const timerNode = document.getElementById("timer");
    const stateNode = document.getElementById("play-state");
    const messageNode = document.getElementById("game-message");
    const canvas = document.getElementById("snake-canvas");
    const target = document.getElementById("reaction-target");
    const memoryBoard = document.getElementById("memory-board");
    const touchControls = document.getElementById("touch-controls");

    let score = 0;
    let startedAt = 0;
    let running = false;
    let timerId;
    let heartbeatId;
    let stopGame = () => {};

    const setScore = (value) => {
        score = Math.max(0, Math.round(value));
        scoreNode.textContent = score;
    };

    const heartbeat = () => fetch("/api/game/heartbeat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({game})
    }).catch(() => {});

    const beginTracking = () => {
        startedAt = Date.now();
        timerId = window.setInterval(() => {
            timerNode.textContent = `${Math.floor((Date.now() - startedAt) / 1000)}s`;
        }, 250);
        heartbeat();
        heartbeatId = window.setInterval(heartbeat, 15000);
    };

    const finish = async (message = "Session saved.") => {
        if (!running) return;
        running = false;
        stopGame();
        window.clearInterval(timerId);
        window.clearInterval(heartbeatId);
        const timePlayed = Math.max(1, Math.floor((Date.now() - startedAt) / 1000));
        stateNode.textContent = "Saving";
        try {
            const response = await fetch("/api/game/finish", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({game, score, time_played: timePlayed})
            });
            if (!response.ok) throw new Error("Unable to save");
            messageNode.textContent = message;
            stateNode.textContent = "Finished";
        } catch {
            messageNode.textContent = "Your game finished, but the result could not be saved.";
            stateNode.textContent = "Offline";
        }
        startPanel.hidden = false;
        startButton.textContent = "Play again";
    };

    const startSnake = () => {
        canvas.hidden = false;
        touchControls.hidden = false;
        const context = canvas.getContext("2d");
        const cells = 18;
        const size = canvas.width / cells;
        let snake = [{x: 8, y: 9}, {x: 7, y: 9}, {x: 6, y: 9}];
        let direction = {x: 1, y: 0};
        let queued = direction;
        let food = {x: 13, y: 9};

        const randomFood = () => {
            do {
                food = {x: Math.floor(Math.random() * cells), y: Math.floor(Math.random() * cells)};
            } while (snake.some(part => part.x === food.x && part.y === food.y));
        };

        const changeDirection = (name) => {
            const map = {up: {x: 0, y: -1}, down: {x: 0, y: 1}, left: {x: -1, y: 0}, right: {x: 1, y: 0}};
            const next = map[name];
            if (next && !(next.x === -direction.x && next.y === -direction.y)) queued = next;
        };

        const keyHandler = (event) => {
            const keys = {ArrowUp: "up", w: "up", ArrowDown: "down", s: "down", ArrowLeft: "left", a: "left", ArrowRight: "right", d: "right"};
            if (keys[event.key]) {
                event.preventDefault();
                changeDirection(keys[event.key]);
            }
        };
        document.addEventListener("keydown", keyHandler);
        touchControls.querySelectorAll("button").forEach(button => {
            button.onclick = () => changeDirection(button.dataset.direction);
        });

        const draw = () => {
            context.fillStyle = "#0b1020";
            context.fillRect(0, 0, canvas.width, canvas.height);
            context.fillStyle = "#ff5f7a";
            context.beginPath();
            context.arc((food.x + .5) * size, (food.y + .5) * size, size * .32, 0, Math.PI * 2);
            context.fill();
            snake.forEach((part, index) => {
                context.fillStyle = index ? "#21b86b" : "#4ade80";
                context.fillRect(part.x * size + 1, part.y * size + 1, size - 2, size - 2);
            });
        };

        const loop = window.setInterval(() => {
            direction = queued;
            const head = {x: snake[0].x + direction.x, y: snake[0].y + direction.y};
            if (head.x < 0 || head.y < 0 || head.x >= cells || head.y >= cells ||
                snake.some(part => part.x === head.x && part.y === head.y)) {
                finish("Snake crashed—score saved.");
                return;
            }
            snake.unshift(head);
            if (head.x === food.x && head.y === food.y) {
                setScore(score + 10);
                randomFood();
            } else {
                snake.pop();
            }
            draw();
        }, 135);
        draw();
        stopGame = () => {
            window.clearInterval(loop);
            document.removeEventListener("keydown", keyHandler);
        };
    };

    const startReaction = () => {
        target.hidden = false;
        let rounds = 0;
        let shownAt = 0;
        let timeout;
        const placeTarget = () => {
            target.classList.remove("visible");
            timeout = window.setTimeout(() => {
                const maxX = Math.max(20, stage.clientWidth - 90);
                const maxY = Math.max(20, stage.clientHeight - 90);
                target.style.left = `${Math.random() * maxX}px`;
                target.style.top = `${Math.random() * maxY}px`;
                shownAt = performance.now();
                target.classList.add("visible");
            }, 500 + Math.random() * 1100);
        };
        target.onclick = () => {
            if (!target.classList.contains("visible")) return;
            const reaction = performance.now() - shownAt;
            setScore(score + Math.max(10, 500 - reaction));
            rounds += 1;
            if (rounds >= 10) finish("Ten targets complete—score saved.");
            else placeTarget();
        };
        placeTarget();
        stopGame = () => {
            window.clearTimeout(timeout);
            target.classList.remove("visible");
        };
    };

    const startMemory = () => {
        memoryBoard.hidden = false;
        const symbols = ["🎮", "👾", "🚀", "⭐", "⚡", "🏆"];
        const cards = [...symbols, ...symbols].sort(() => Math.random() - .5);
        let open = [];
        let matched = 0;
        let moves = 0;
        memoryBoard.innerHTML = "";
        cards.forEach((symbol, index) => {
            const card = document.createElement("button");
            card.type = "button";
            card.className = "memory-card";
            card.dataset.symbol = symbol;
            card.dataset.index = index;
            card.textContent = "?";
            card.onclick = () => {
                if (!running || open.length === 2 || card.classList.contains("matched") || open.includes(card)) return;
                card.textContent = symbol;
                card.classList.add("open");
                open.push(card);
                if (open.length === 2) {
                    moves += 1;
                    if (open[0].dataset.symbol === open[1].dataset.symbol) {
                        open.forEach(item => item.classList.add("matched"));
                        open = [];
                        matched += 2;
                        setScore(600 - moves * 20);
                        if (matched === cards.length) finish("Board cleared—score saved.");
                    } else {
                        window.setTimeout(() => {
                            open.forEach(item => {
                                item.textContent = "?";
                                item.classList.remove("open");
                            });
                            open = [];
                        }, 650);
                    }
                }
            };
            memoryBoard.appendChild(card);
        });
        stopGame = () => {};
    };

    startButton.addEventListener("click", () => {
        setScore(0);
        messageNode.textContent = "";
        running = true;
        stateNode.textContent = "Playing";
        startPanel.hidden = true;
        canvas.hidden = true;
        target.hidden = true;
        memoryBoard.hidden = true;
        touchControls.hidden = true;
        beginTracking();
        if (game === "snake") startSnake();
        if (game === "reaction") startReaction();
        if (game === "memory") startMemory();
    });
    finishButton.addEventListener("click", () => finish());
});
