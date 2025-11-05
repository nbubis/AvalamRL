let ws;
let board_data = [];

const MoveState = {
    WAITING_FOR_SOURCE: 'WAITING_FOR_SOURCE',
    WAITING_FOR_TARGET: 'WAITING_FOR_TARGET'
};
let currentState = MoveState.WAITING_FOR_SOURCE;
let sourceLocation = null;

margin = 50;
spacing = 50;
ellipse_ratio = 0.9;
center_game_text = "AvalamRL";
game_text_color = 40
current_scores = [0, 0];
legal_move_num = 0;

function setup() {
    createCanvas(2 * margin + 9 * spacing, 2 * margin + 9 * spacing);

    ws = new WebSocket("ws://localhost:8765");

    for (let element of document.getElementsByClassName("p5Canvas")) {
        element.addEventListener("contextmenu", (e) => e.preventDefault());
    }
    ws.onmessage = (event) => {
        let data = JSON.parse(event.data);
        if ("board_pieces" in data) {
            board_data = data.board_pieces;
        }
        if ("error" in data) {
            console.log(data.error);
        }
        if ("legal_move_num" in data && "scores" in data) {
            current_scores = data.scores;
            legal_move_num = data.legal_move_num;
        }
    };
    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

function boardPositionToPixel(x) {
    return margin + x * spacing + spacing / 2
}

function PixelToBoardPosition(pixelX, pixelY) {
    x = Math.round((pixelX - margin) / spacing - 0.5);
    y = Math.round((pixelY - margin) / spacing - 0.5);
    return { x, y };
}

function draw() {
    height_shift = 5;
    diameter = spacing * 0.8;
    clear();
    background(50);
    if (legal_move_num === 0) {
        center_game_text = "Game Over";
    }
    textSize(36);
    textStyle(BOLD);
    textAlign(CENTER, CENTER);
    fill(game_text_color);
    text(center_game_text, boardPositionToPixel(4), boardPositionToPixel(9));
    fill(200, 100, 100);
    text(current_scores[0], boardPositionToPixel(-1), boardPositionToPixel(4));
    fill(200, 200, 100);
    text(current_scores[1], boardPositionToPixel(9), boardPositionToPixel(4));


    if (sourceLocation) {
        noFill();
        stroke(80);
        strokeWeight(5);
        ellipse(boardPositionToPixel(sourceLocation.x), boardPositionToPixel(sourceLocation.y), spacing, spacing * ellipse_ratio);
    }
    for (let i = 0; i < 5; i++) {
        for (let tile of board_data) {
            let drawX = boardPositionToPixel(tile.x);
            let drawY = boardPositionToPixel(tile.y);

            strokeWeight(1);
            if (tile.state[0] === 0) {
                stroke(45);
                fill(45);
                ellipse(drawX, drawY, diameter / 2, diameter / 2 * ellipse_ratio);
            }

            if (tile.state[i] === 0) {
                continue;
            }
            if (tile.state[i] === 1) {
                stroke(140, 70, 70);
                fill(200, 100, 100);
            }
            if (tile.state[i] === -1) {
                stroke(140, 140, 70);
                fill(200, 200, 100);
            }
            for (let h = 0; h < 6; h++) {
                ellipse(drawX, drawY - h / 2 - height_shift * i, diameter, diameter * ellipse_ratio);
            }

            if (tile.state[i] === 1) {
                stroke(180, 90, 90);
                fill(180, 90, 90);
            } else if (tile.state[i] === -1) {
                stroke(180, 180, 90);
                fill(180, 180, 90);
            }
            ellipse(drawX, drawY - 2.5 - height_shift * i, diameter / 2, diameter / 2 * ellipse_ratio);
        }
    }
}



function mousePressed() {

    if (currentState === MoveState.WAITING_FOR_SOURCE) {
        if (mouseButton === RIGHT) {
            return;
        }
        sourceLocation = PixelToBoardPosition(mouseX, mouseY);
        currentState = MoveState.WAITING_FOR_TARGET;
    } else if (currentState === MoveState.WAITING_FOR_TARGET) {
        if (mouseButton === RIGHT) {
            sourceLocation = null;
            currentState = MoveState.WAITING_FOR_SOURCE;
            return;
        }
        let targetLocation = PixelToBoardPosition(mouseX, mouseY);
        const move = {
            source: { x: sourceLocation.x, y: sourceLocation.y },
            target: { x: targetLocation.x, y: targetLocation.y }
        };

        ws.send(JSON.stringify(move));
        sourceLocation = null;
        currentState = MoveState.WAITING_FOR_SOURCE; // Use the constant
    }

};
