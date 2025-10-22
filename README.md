# BMS - Business Management System

A scalable Business Management System built with Flet 0.22.1, featuring a modular architecture for easy maintenance and expansion.

## Architecture Overview

The application follows a clean, modular architecture with clear separation of concerns:

```
BMS/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── src/                   # Source code directory
    ├── __init__.py
    ├── config.py          # Configuration constants and settings
    ├── models/            # Data models
    │   ├── __init__.py
    │   ├── base.py        # Base model class
    │   ├── handover.py    # Handover model
    │   ├── requirement.py # Requirement model
    │   ├── issue.py       # Issue model
    │   └── test_suite.py  # Test Suite model
    ├── services/          # Business logic layer
    │   ├── __init__.py
    │   ├── database.py    # Database operations
    │   └── bms_service.py # Main business logic
    ├── ui/                # User interface layer
    │   ├── __init__.py
    │   ├── main_app.py    # Main application class
    │   ├── components/    # Reusable UI components
    │   │   ├── __init__.py
    │   │   ├── dialogs.py # Form dialogs
    │   │   └── cards.py   # Data display cards
    │   └── views/         # View components
    │       ├── __init__.py
    │       ├── dashboard.py    # Dashboard view
    │       └── handovers.py    # Handovers view
    └── utils/             # Utility functions
        ├── __init__.py
        ├── export.py      # Export functionality
        └── validators.py  # Form validation
```

## Key Features

### 🏗️ Modular Architecture
- **Models**: Clean data models with validation
- **Services**: Business logic separated from UI
- **UI Components**: Reusable, maintainable UI components
- **Configuration**: Centralized configuration management

### 📊 Core Functionality
- **Dashboard**: Statistics and recent activities overview
- **Handovers**: Team handover management
- **Requirements**: System requirements tracking
- **Issues**: Issue tracking and management
- **Test Suites**: Test execution results management

### 🎨 User Experience
- **Responsive Design**: Works on desktop and web
- **Dark/Light Theme**: Toggle between themes
- **Data Export**: CSV export functionality
- **Form Validation**: Comprehensive input validation
- **Real-time Updates**: Live data refresh

### 🔧 Technical Features
- **SQLite Database**: Local data storage
- **Type Hints**: Full type annotation support
- **Error Handling**: Robust error management
- **Validation**: Input validation and data integrity
- **Export System**: Flexible data export capabilities

## Installation

1. **Clone or download the project**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Starting the Application
```bash
python main.py
```

The application will start with a web interface that can be accessed in your browser.

### Key Features

1. **Dashboard**: View statistics and recent activities
2. **Handovers**: Manage team handovers with filtering
3. **Requirements**: Track system requirements
4. **Issues**: Report and manage issues
5. **Test Suites**: Monitor test execution results

### Data Management
- **Add**: Click "New" buttons to add items
- **Edit**: Click "Edit" buttons to modify items
- **Delete**: Click "Delete" buttons to remove items
- **Filter**: Use dropdown filters to view specific data
- **Export**: Use "Export to CSV" buttons to download data

## Architecture Benefits

### 🚀 Scalability
- **Modular Design**: Easy to add new features
- **Separation of Concerns**: Clear boundaries between layers
- **Reusable Components**: UI components can be reused
- **Configuration Management**: Easy to modify settings

### 🛠️ Maintainability
- **Clean Code**: Well-structured, readable code
- **Type Safety**: Full type hints for better IDE support
- **Validation**: Comprehensive input validation
- **Error Handling**: Robust error management

### 🔧 Extensibility
- **Plugin Architecture**: Easy to add new modules
- **Service Layer**: Business logic is centralized
- **UI Components**: Reusable UI building blocks
- **Database Layer**: Abstracted data access

## Development

### Adding New Features

1. **Create Model**: Add new model in `src/models/`
2. **Add Service**: Implement business logic in `src/services/`
3. **Create UI**: Build UI components in `src/ui/`
4. **Update Config**: Add constants to `src/config.py`

### Code Structure

- **Models**: Data classes with validation
- **Services**: Business logic and data operations
- **UI**: User interface components and views
- **Utils**: Helper functions and utilities
- **Config**: Application configuration

## Dependencies

- **Flet 0.22.1**: Modern Python UI framework
- **SQLite**: Built-in database support
- **Standard Library**: No external dependencies beyond Flet

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Real-time notifications
- [ ] Advanced reporting and analytics
- [ ] API integration capabilities
- [ ] Mobile app support
- [ ] Cloud database support
- [ ] Advanced filtering and search
- [ ] Data visualization charts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.
