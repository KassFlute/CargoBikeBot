# Bike Reservation Bot

This project is a Telegram bot for managing bike reservations. Users can create, view, and cancel reservations through the bot. The bot interacts with CSV files to store data about users, bikes, and reservations.

## Features

- Create new bike reservations
- View existing reservations
- Cancel reservations
- Manage user information
- Manage bike information

## Project Structure
- `src/main.py`: Contains the main logic for the Telegram bot.
- `src/storage.py`: Contains classes for managing storage of users, bikes, and reservations in CSV files.
- `storage/`: Directory containing the CSV files used for storing data.
- `tests/`: Directory for unit tests.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/bike-reservation-bot.git
    cd bike-reservation-bot
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up your Telegram bot token:
    - Create a `.env` file in the root directory of the project.
    - Add your bot token to the `.env` file:
      ```
      BOT_TOKEN=your-telegram-bot-token
      ```

## Usage

1. Run the bot:
    ```sh
    python main.py
    ```

2. Interact with the bot on Telegram using the commands:
    - `/start`: Start the bot and receive a welcome message.
    - `/help`: Get help information about the bot.
    - `/res`: Manage or create your reservations.

## Storage

The bot uses CSV files to store data:
- `storage/bikes.csv`: Stores information about bikes.
- `storage/reservations.csv`: Stores information about reservations.
- `storage/users.csv`: Stores information about users.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
