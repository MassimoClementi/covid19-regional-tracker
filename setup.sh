echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating the virtual environment..."
source venv/bin/activate

echo "Installing the required packages..."
pip3 install -r requirements.txt
