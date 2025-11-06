import numpy as np
import asyncio
import websockets
import random
import json


def init_board_pieces():
    board_pieces = np.zeros((9, 9, 5), dtype=np.int8)

    fill_ranges = [
        range(2, 4),
        range(1, 5),
        range(1, 7),
        range(1, 9),
        range(0, 9),
        range(0, 8),
        range(2, 8),
        range(4, 8),
        range(5, 7),
    ]

    for i in range(9):
        for j in range(9):
            if j not in fill_ranges[i]:
                continue
            if (i + j) % 2 == 0:
                board_pieces[i, j, 0] = 1
            else:
                board_pieces[i, j, 0] = -1
    board_pieces[4, 4, 0] = 0
    return board_pieces


def board_pieces_json(board_pieces):
    pieces_list = []
    for i in range(9):
        for j in range(9):
            pieces_list.append({"x": i, "y": j, "state": board_pieces[i, j].tolist()})
    return json.dumps({"board_pieces": pieces_list})


def get_legal_moves(board_pieces):
    moves = []
    for source_i in range(9):
        for source_j in range(9):
            if board_pieces[source_i, source_j, 0] == 0:
                continue
            for target_i in range(max(0, source_i - 1), min(9, source_i + 2)):
                for target_j in range(max(0, source_j - 1), min(9, source_j + 2)):
                    if (source_i == target_i and source_j == target_j) or board_pieces[target_i, target_j, 0] == 0:
                        continue
                    source_n = np.sum(np.abs(board_pieces[source_i, source_j]))
                    target_n = np.sum(np.abs(board_pieces[target_i, target_j]))
                    if source_n + target_n <= 5:
                        moves.append(((source_i, source_j), (target_i, target_j)))
    return moves


def get_scores(board_pieces):
    legal_moves = get_legal_moves(board_pieces)

    scores = [0, 0]
    for i in range(9):
        for j in range(9):
            if all((i, j) != target for source, target in legal_moves):
                last = next((x for x in reversed(list(board_pieces[i, j])) if x != 0), 0)
                if last == 1:
                    scores[0] += 1
                elif last == -1:
                    scores[1] += 1
    return scores


def apply_move(board_pieces, move):
    (source_i, source_j), (target_i, target_j) = move
    source_tower = board_pieces[source_i, source_j]
    target_n = np.sum(np.abs(board_pieces[target_i, target_j]))
    board_pieces[target_i, target_j, target_n:] = source_tower[: 5 - target_n]
    board_pieces[source_i, source_j] = np.zeros(5, dtype=np.int8)
    return board_pieces


def naive_player(board_pieces):
    legal_moves = get_legal_moves(board_pieces)
    current_scores = get_scores(board_pieces)
    best_score_diff = 0
    best_move = None
    if not legal_moves:
        return None
    for move1 in legal_moves:
        new_board1 = apply_move(board_pieces.copy(), move1)
        new_scores = get_scores(new_board1)
        score_diff = (new_scores[0] - current_scores[0]) - (new_scores[1] - current_scores[1])
        if score_diff > best_score_diff:
            best_move = move1
            best_score_diff = score_diff
    if best_move is not None:
        return best_move
    return random.choice(legal_moves)


async def handler(websocket):
    try:
        board_pieces = init_board_pieces()
        legal_moves = get_legal_moves(board_pieces)
        await websocket.send(json.dumps(({"legal_move_num": len(legal_moves), "scores": get_scores(board_pieces)})))

        await websocket.send(board_pieces_json(board_pieces))

        async for message in websocket:
            data = json.loads(message)
            suggested_move = ((data["source"]["x"], data["source"]["y"]), (data["target"]["x"], data["target"]["y"]))
            legal_moves = get_legal_moves(board_pieces)
            if suggested_move in legal_moves:
                board_pieces = apply_move(board_pieces, suggested_move)
                await websocket.send(board_pieces_json(board_pieces))
                ai_move = naive_player(board_pieces)
                if ai_move:
                    board_pieces = apply_move(board_pieces, ai_move)
                    await websocket.send(board_pieces_json(board_pieces))
                legal_moves = get_legal_moves(board_pieces)

            else:
                await websocket.send(json.dumps({"error": f"Illegal move {str(suggested_move)}"}))

            await websocket.send(json.dumps(({"legal_move_num": len(legal_moves), "scores": get_scores(board_pieces)})))

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")


async def main():
    # Start the server on localhost port 8765
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
