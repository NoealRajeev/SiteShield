# SafeSite

SafeSite is an integrated safety solution for construction sites that combines an entry point attendance system with visual recognition technology to ensure workers are equipped with the necessary safety gear. This project aims to enhance safety, ensure compliance with safety regulations, and streamline attendance tracking.

## Features

- **RFID-based Attendance System**: Track worker entry and exit times using RFID cards.
- **Visual Recognition**: Verify that workers are wearing required safety gear such as helmets and high-visibility vests.
- **Data Management**: Store and manage attendance records and safety compliance data in a MySQL database.
- **Web Interface**: Access and manage data through a user-friendly web interface built with Flask.

## Technologies Used

- **Backend and Frontend**: Flask (Python)
- **Database**: MySQL
- **Hardware**: RFID reader (MFRC522), Raspberry Pi
- **Libraries**: OpenCV for visual recognition, Flask-CORS for handling CORS, Requests for HTTP requests

## Installation

### Prerequisites

- Python 3.x
- MySQL

### Backend and Frontend Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/safesite.git
    cd safesite
    ```

2. Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. Configure MySQL database:
    - Create a MySQL database named `projects`.
    - Update the `db_config` in `app.py` with your MySQL user and password.

4. Start the Flask server:
    ```bash
    python app.py
    ```

### Running the Application

- Ensure the Flask server is running.
- Open your browser and navigate to `http://localhost:5001` to access the SafeSite web interface.

## Usage

1. **Register Users**: Add worker details, including their card ID, name, and designation, to the system.
2. **RFID Scanning**: Workers scan their RFID cards at the entry point. The system records their entry time and checks their safety gear.
3. **Exit Recording**: When workers leave the site, they scan their RFID cards again to record their exit time.
4. **Data Management**: Use the web interface to view and manage attendance records and safety compliance data.

## Contribution

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the MIT License.

---

**SafeSite** - Enhancing construction site safety through technology.
