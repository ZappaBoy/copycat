from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
from pynput.mouse import Listener as MouseListener, Button

from copycat.models.history.history import History
from copycat.models.move.move import Move
from copycat.models.move.move_type import MoveType
from copycat.shared.utils.generic import get_timestamp
from copycat.shared.utils.logger import Logger


class ListenersService:
    pooling: int = 0.03
    exit_key: Key = Key.esc

    def __init__(self):
        self.logger = Logger()
        self.mouse_listener = None
        self.keyboard_listener = None
        self.history: History = History()
        self.last_mouse_move_time: float = get_timestamp()

    def create_listeners(self) -> None:
        self.mouse_listener = MouseListener(on_click=self.on_click, on_scroll=self.on_scroll, on_move=self.on_move)
        self.keyboard_listener = KeyboardListener(on_press=self.on_press, on_release=self.on_release)

    def get_history(self) -> History:
        return self.history

    def clean_history(self) -> None:
        self.history = History()

    def start_recording(self) -> None:
        self.history.start()
        self.start_listeners()

    def stop_recording(self) -> None:
        self.history.stop()
        self.stop_listener()

    def start_listeners(self) -> None:
        self.create_listeners()
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_listener(self) -> None:
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        self.logger.info("Listeners stopped")

    def on_click(self, x: int, y: int, button: Button, pressed: bool) -> None:
        self.logger.debug(f'Mouse clicked at ({x}, {y}) with {button} {pressed}')
        move = Move(move_type=MoveType.MOUSE_CLICK, x=x, y=y, button_name=button.name, pressed=pressed)
        self.add_move(move)

    def on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        self.logger.debug(f'Mouse scrolled at ({x}, {y})({dx}, {dy})')
        move = Move(move_type=MoveType.MOUSE_SCROLL, x=x, y=y, dx=dx, dy=dy)
        self.add_move(move)

    def on_press(self, key: Key | KeyCode) -> None:
        self.logger.debug(f"Key pressed: {key}")
        key_code, key_name = self.get_key(key)
        if key == self.exit_key:
            self.logger.info("Ignoring Exit Key On Press")
            return
        move = Move(move_type=MoveType.KEY_PRESS, key_code=key_code, key_name=key_name)
        self.add_move(move)

    def on_release(self, key: Key | KeyCode) -> None:
        self.logger.debug(f"Key released: {key}")
        key_code, key_name = self.get_key(key)
        if key == self.exit_key:
            self.logger.info("Ignoring Exit Key On Release")
            return
        move = Move(move_type=MoveType.KEY_RELEASED, key_code=key_code, key_name=key_name)
        self.add_move(move)

    def on_move(self, x: int, y: int) -> None:
        self.logger.debug(f"Mouse moved to ({x}, {y})")
        now = get_timestamp()
        time_diff = now - self.last_mouse_move_time
        if time_diff > self.pooling:
            self.logger.debug(f"Mouse move saved to history")
            self.last_mouse_move_time = now + self.pooling
            move = Move(move_type=MoveType.MOUSE_MOVE, x=x, y=y)
            self.add_move(move)

    def add_move(self, move: Move) -> None:
        self.history.add_move(move)

    @staticmethod
    def get_key(key: Key | KeyCode) -> tuple[str, str]:
        key_code = None
        key_name = None
        if isinstance(key, KeyCode):
            key_code = key.char
        elif isinstance(key, Key):
            key_name = key.name
        return key_code, key_name
