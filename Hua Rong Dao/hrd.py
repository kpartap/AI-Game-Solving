import argparse
import heapq
#====================================================================================

char_single = '2'

class Piece:
    """
    This represents a piece on the Hua Rong Dao puzzle.
    """

    def __init__(self, is_2_by_2, is_single, coord_x, coord_y, orientation):
        """
        :param is_2_by_2: True if the piece is a 2x2 piece and False otherwise.
        :type is_2_by_2: bool
        :param is_single: True if this piece is a 1x1 piece and False otherwise.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        :param orientation: The orientation of the piece (one of 'h' or 'v') 
            if the piece is a 1x2 piece. Otherwise, this is None
        :type orientation: str
        """

        self.is_2_by_2 = is_2_by_2
        self.is_single = is_single
        self.coord_x = coord_x
        self.coord_y = coord_y
        self.orientation = orientation

    def set_coords(self, coord_x, coord_y):
        """
        Move the piece to the new coordinates. 

        :param coord: The new coordinates after moving.
        :type coord: int
        """

        self.coord_x = coord_x
        self.coord_y = coord_y

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.is_2_by_2, self.is_single, \
            self.coord_x, self.coord_y, self.orientation)

class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, height, pieces):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 4
        self.height = height
        self.pieces = pieces

        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid()

        self.blanks = []

    # customized eq for object comparison.
    def __eq__(self, other):
        if isinstance(other, Board):
            return self.grid == other.grid
        return False


    def __construct_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """

        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append('.')
            self.grid.append(line)

        for piece in self.pieces:
            if piece.is_2_by_2:
                self.grid[piece.coord_y][piece.coord_x] = '1'
                self.grid[piece.coord_y][piece.coord_x + 1] = '1'
                self.grid[piece.coord_y + 1][piece.coord_x] = '1'
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = '1'
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = char_single
            else:
                if piece.orientation == 'h':
                    self.grid[piece.coord_y][piece.coord_x] = '<'
                    self.grid[piece.coord_y][piece.coord_x + 1] = '>'
                elif piece.orientation == 'v':
                    self.grid[piece.coord_y][piece.coord_x] = '^'
                    self.grid[piece.coord_y + 1][piece.coord_x] = 'v'
      
    def display(self):
        """
        Print out the current board.

        """
        for i, line in enumerate(self.grid):
            for ch in line:
                print(ch, end='')
            print()
        

class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces. 
    State has a Board and some extra information that is relevant to the search: 
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, board, g=0, h=0, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param hfn: The heuristic function.
        :type hfn: Optional[Heuristic]
        :param f: The f value of current state.
        :type f: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.g = g
        self.h = h
        self.f = g + h
        self.parent = parent

    def __lt__(self, other):
        """
        Comparison function to help with heap-based priority queues (A*).
        """
        return self.f < other.f

def is_goal_state(current_state, goal_board):
    """
    Check if the current state is the goal state.
    
    :param current_state: The current state of the board.
    :param goal_board: The goal board state.
    :return: True if current state matches the goal, False otherwise.
    """
    return current_state.board.grid == goal_board.grid


def find_empty_spaces(board):
    """
    Find all empty spaces ('.') on the board.
    
    :param board: The board object.
    :return: A list of coordinates (x, y) for all empty spaces.
    """
    empty_spaces = []
    for y in range(board.height):
        for x in range(board.width):
            if board.grid[y][x] == '.':
                empty_spaces.append((x, y))
    return empty_spaces


def clear_piece_from_grid(grid, piece):
    """
    Clears the piece from the grid, replacing the piece's current location
    with '.' to indicate empty spaces.

    :param grid: The grid representing the board.
    :type grid: List[List[str]]
    :param piece: The piece to be cleared from the grid.
    :type piece: Piece
    """

    x = piece.coord_x
    y = piece.coord_y

    if piece.is_2_by_2:
        grid[y][x] = '.'
        grid[y][x + 1] = '.'
        grid[y + 1][x] = '.'
        grid[y + 1][x + 1] = '.'

    elif piece.is_single:
        grid[y][x] = '.'

    else:
        if piece.orientation == 'h':
            grid[y][x] = '.'
            grid[y][x + 1] = '.'
        elif piece.orientation == 'v':
            grid[y][x] = '.'
            grid[y + 1][x] = '.'


def manhattan_distance(board, goal_board):
    """
    Calculate the Manhattan distance heuristic between the current state and the goal state.

    :param board: The current board (2D list).
    :param goal_board: The goal board (2D list).
    :return: The Manhattan distance for the 2x2 piece.
    """
    indexes = []
    total_dist = 0
    for piece in board.pieces:
        for goal_piece in goal_board.pieces:
            if piece.is_2_by_2 == goal_piece.is_2_by_2 and piece.is_single == goal_piece.is_single and piece.orientation == goal_piece.orientation:
                if goal_board.pieces.index(goal_piece) not in indexes:
                    total_dist += abs(piece.coord_x - goal_piece.coord_x) + abs(piece.coord_y - goal_piece.coord_y)
                    indexes.append(goal_board.pieces.index(goal_piece))
                    break

    return total_dist



def is_valid_move(piece, board, new_x, new_y, empty_spaces, move):
    """
    Check if moving a piece to a new position is valid.
    
    :param piece: The piece being moved.
    :param board: The current board.
    :param new_x: The new x-coordinate.
    :param new_y: The new y-coordinate.
    :param empty_spaces: List of empty spaces on the board.
    :param move: direction of the move taking place
    :return: True if the move is valid, False otherwise.
    """
    if new_x < 0 or new_x >= board.width or new_y < 0 or new_y >= board.height:
        return False
    needed_spaces = []
    if piece.is_2_by_2:
        if move == 'left':
            needed_spaces = [(new_x, new_y), (new_x, new_y + 1)]
        if move == 'up':
            needed_spaces = [(new_x, new_y), (new_x + 1, new_y)]
        if move == 'down':
            if new_x + 1 < 0 or new_x + 1 >= board.width or new_y + 1 < 0 or new_y + 1 >= board.height:
                return False
            needed_spaces = [(new_x, new_y + 1), (new_x + 1, new_y + 1)]
        if move == 'right':
            if new_x + 1 < 0 or new_x + 1 >= board.width or new_y + 1 < 0 or new_y + 1 >= board.height:
                return False
            needed_spaces = [(new_x + 1, new_y), (new_x + 1, new_y + 1)]
    elif piece.is_single:
        needed_spaces = [(new_x, new_y)]
    elif piece.orientation == 'h':
        if move == 'up':
            if new_x + 1 < 0 or new_x + 1 >= board.width:
                return False
            needed_spaces = [(new_x, new_y), ((new_x + 1, new_y))]
        if move == 'down':
            if new_x + 1 < 0 or new_x + 1 >= board.width:
                return False
            needed_spaces = [(new_x, new_y), ((new_x + 1, new_y))]
        if move == 'left':
            needed_spaces = [(new_x, new_y)]
        if move == 'right':
            if new_x + 1 < 0 or new_x + 1 >= board.width:
                return False
            needed_spaces = [(new_x + 1, new_y)]
    elif piece.orientation == 'v':
        if move == 'up':
            needed_spaces = [(new_x, new_y)]
        if move == 'down':
            if new_y + 1 < 0 or new_y + 1 >= board.height:
                return False
            needed_spaces = [(new_x, new_y + 1)]
        if move == 'left':
            if new_y + 1 < 0 or new_y + 1 >= board.height:
                return False
            needed_spaces = [(new_x, new_y), ((new_x, new_y + 1))]  
        if move == 'right':
            if new_y + 1 < 0 or new_y + 1 >= board.height:
                return False
            needed_spaces = [(new_x, new_y), ((new_x, new_y + 1))]      
    
    if needed_spaces == []:
        return False
    for space in needed_spaces:
        if space not in empty_spaces:
            return False
    
    return True

def move_piece(board, piece, new_x, new_y):
    """
    Move a piece to a new location and return a new board.
    
    :param board: The current board.
    :param piece: The piece to be moved.
    :param new_x: The new x coordinate.
    :param new_y: The new y coordinate.
    :return: A new board with the piece moved.
    """
    new_grid = [row[:] for row in board.grid]
    clear_piece_from_grid(new_grid, piece)

    if piece.is_2_by_2:
        new_grid[new_y][new_x] = '1'
        new_grid[new_y][new_x + 1] = '1'
        new_grid[new_y + 1][new_x] = '1'
        new_grid[new_y + 1][new_x + 1] = '1'
    elif piece.is_single:
        new_grid[new_y][new_x] = '2'
    else:
        if piece.orientation == 'h':
            new_grid[new_y][new_x] = '<'
            new_grid[new_y][new_x + 1] = '>'
        elif piece.orientation == 'v':
            new_grid[new_y][new_x] = '^'
            new_grid[new_y + 1][new_x] = 'v'

    new_board = Board(board.height, board.pieces)
    new_board.grid = new_grid
    return new_board

def generate_successors(current_state, goal_board):
    """
    Generate valid successor states by moving pieces to adjacent empty spaces.
    
    :param current_state: The current state of the board.
    :param goal_board: the final goal board
    :return: A list of successor states.
    """
    successors = []
    empty_spaces = find_empty_spaces(current_state.board)

    for piece in current_state.board.pieces:
        moves = [('up', 0, -1), ('down', 0, 1), ('left', -1, 0), ('right', 1, 0)]
        
        for move, dx, dy in moves:
            new_x, new_y = piece.coord_x + dx, piece.coord_y + dy
            if is_valid_move(piece, current_state.board, new_x, new_y, empty_spaces, move):
                point = current_state.board.pieces.index(piece)
                new_pieces = []
                for element in current_state.board.pieces:
                    new_pieces.append(Piece(element.is_2_by_2, element.is_single, element.coord_x, element.coord_y, element.orientation))
                new_pieces[point].coord_x = new_x
                new_pieces[point].coord_y = new_y
                new_board = Board(current_state.board.height, new_pieces)
                new_state = State(new_board, current_state.g + 1, manhattan_distance(new_board, goal_board), current_state)
                successors.append(new_state)

    return successors



def dfs(initial_state, goal_board):
    """
    Perform Depth-First Search (DFS) to find a solution.
    
    :param initial_state: The starting state.
    :param goal_board: The goal state board.
    :return: The solution path if found, otherwise "No solution".
    """
    stack = [initial_state]
    explored = set()

    while stack:
        current_state = stack.pop()

        if is_goal_state(current_state, goal_board):
            return backtrack_solution(current_state)

        explored.add(str(current_state.board.grid))

        successors = generate_successors(current_state, goal_board)

        for successor in successors:
            if str(successor.board.grid) not in explored:
                stack.append(successor)

    return "No solution"

def a_star(initial_state, goal_board):
    """
    Perform A* Search to find the optimal solution.
    
    :param initial_state: The starting state.
    :param goal_board: The goal state board.
    :return: The solution path if found, otherwise "No solution".
    """
    frontier = []
    heapq.heappush(frontier, (initial_state.f, initial_state))
    explored = set()

    while frontier:
        _, current_state = heapq.heappop(frontier)

        if is_goal_state(current_state, goal_board):
            return backtrack_solution(current_state)

        explored.add(str(current_state.board.grid))

        successors = generate_successors(current_state, goal_board)

        for successor in successors:
            if str(successor.board.grid) not in explored:
                heapq.heappush(frontier, (successor.f, successor))

    return "No solution"

def backtrack_solution(goal_state):
    """
    Trace back the solution path from the goal state to the initial state.
    
    :param goal_state: The goal state.
    :return: A list of board configurations representing the solution path.
    """
    solution_path = []
    current_state = goal_state

    while current_state is not None:
        solution_path.append(current_state.board)
        current_state = current_state.parent

    solution_path.reverse()
    return solution_path


def write_solution_to_file(solution_path, outputfile):
    """
    Write the solution path to the output file.
    
    :param solution_path: The list of boards in the solution path.
    :param outputfile: The file to write the solution to.
    """
    with open(outputfile, 'w') as f:
        for board in solution_path:
            f.write(grid_to_string(board.grid))
            f.write("\n")


def read_from_file(filename):
    """
    Load initial board from a given file.

    :param filename: The name of the given file.
    :type filename: str
    :return: A loaded board
    :rtype: Board
    """

    puzzle_file = open(filename, "r")

    line_index = 0
    pieces = []
    final_pieces = []
    final = False
    found_2by2 = False
    finalfound_2by2 = False
    height_ = 0

    for line in puzzle_file:
        height_ += 1
        if line == '\n':
            if not final:
                height_ = 0
                final = True
                line_index = 0
            continue
        if not final: #initial board
            for x, ch in enumerate(line):
                if ch == '^': # found vertical piece
                    pieces.append(Piece(False, False, x, line_index, 'v'))
                elif ch == '<': # found horizontal piece
                    pieces.append(Piece(False, False, x, line_index, 'h'))
                elif ch == char_single:
                    pieces.append(Piece(False, True, x, line_index, None))
                elif ch == '1':
                    if found_2by2 == False:
                        pieces.append(Piece(True, False, x, line_index, None))
                        found_2by2 = True
        else: #goal board
            for x, ch in enumerate(line):
                if ch == '^': # found vertical piece
                    final_pieces.append(Piece(False, False, x, line_index, 'v'))
                elif ch == '<': # found horizontal piece
                    final_pieces.append(Piece(False, False, x, line_index, 'h'))
                elif ch == char_single:
                    final_pieces.append(Piece(False, True, x, line_index, None))
                elif ch == '1':
                    if finalfound_2by2 == False:
                        final_pieces.append(Piece(True, False, x, line_index, None))
                        finalfound_2by2 = True
        line_index += 1
        
    puzzle_file.close()
    board = Board(height_, pieces)
    goal_board = Board(height_, final_pieces)
    return board, goal_board


def grid_to_string(grid):
    string = ""
    for i, line in enumerate(grid):
        for ch in line:
            string += ch
        string += "\n"
    return string


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzles."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    parser.add_argument(
        "--algo",
        type=str,
        required=True,
        choices=['astar', 'dfs'],
        help="The searching algorithm."
    )
    args = parser.parse_args()

    # read the board from the file
    board, goal_board = read_from_file(args.inputfile)

    initial_state = State(board, h=manhattan_distance(board, goal_board))

    if args.algo == 'dfs':
        solution = dfs(initial_state, goal_board)
    elif args.algo == 'astar':
        solution = a_star(initial_state, goal_board)

    if solution != "No solution":
        write_solution_to_file(solution, args.outputfile)
    else:
        with open(args.outputfile, 'w') as f:
            f.write("No solution\n")

