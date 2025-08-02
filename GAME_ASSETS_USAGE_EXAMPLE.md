# Game Assets Integration Guide

## Overview
The game configuration APIs now support an optional `game_assets` field that allows you to upload and extract zip files containing game assets.

## API Usage Examples

### 1. Create Game Configuration with Assets

**POST** `/game-configuration`

```json
{
  "game_name": "My Awesome Game",
  "game_description": "An exciting game with amazing graphics",
  "game_type_name": 1,
  "game_icon": {
    "uploadfilename": "file_685f794d79d0e77a1e25d5a2_icon.png",
    "original_filename": "game_icon.png",
    "uploadurl": "public/temp_uploads/file_685f794d79d0e77a1e25d5a2_icon.png",
    "filesize_kb": 45.2
  },
  "game_banner": [
    {
      "uploadfilename": "file_685f794d79d0e77a1e25d5a2_banner1.jpg",
      "original_filename": "banner1.jpg",
      "uploadurl": "public/temp_uploads/file_685f794d79d0e77a1e25d5a2_banner1.jpg",
      "filesize_kb": 120.5
    }
  ],
  "game_assets": {
    "uploadfilename": "file_685f794d79d0e77a1e25d5a2_018f5646.zip",
    "original_filename": "game_assets.zip",
    "uploadurl": "public/temp_uploads/file_685f794d79d0e77a1e25d5a2_018f5646.zip",
    "filesize_kb": 16.86
  }
}
```

**Response:**
```json
{
  "message": "Game created successfully"
}
```

### 2. Update Game Configuration with Assets

**PUT** `/game-configuration`

```json
{
  "id": "507f1f77bcf86cd799439011",
  "game_name": "My Awesome Game Updated",
  "game_description": "An exciting game with amazing graphics and new features",
  "game_type_name": 2,
  "game_icon": {
    "uploadfilename": "file_685f794d79d0e77a1e25d5a2_icon_new.png",
    "original_filename": "icon_new.png",
    "uploadurl": "public/temp_uploads/file_685f794d79d0e77a1e25d5a2_icon_new.png",
    "filesize_kb": 52.1
  },
  "game_banner": [
    {
      "uploadfilename": "file_685f794d79d0e77a1e25d5a2_banner2.jpg",
      "original_filename": "banner2.jpg",
      "uploadurl": "public/temp_uploads/file_685f794d79d0e77a1e25d5a2_banner2.jpg",
      "filesize_kb": 135.8
    }
  ],
  "game_assets": {
    "uploadfilename": "file_685f794d79d0e77a1e25d5a2_new_assets.zip",
    "original_filename": "new_assets.zip",
    "uploadurl": "public/temp_uploads/file_685f794d79d0e77a1e25d5a2_new_assets.zip",
    "filesize_kb": 25.3
  }
}
```

**Response:**
```json
{
  "message": "Game configuration updated successfully"
}
```

### 3. Get Game Configuration (includes assets info)

**GET** `/game-configuration/{game_id}`

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "game_name": "My Awesome Game",
  "game_description": "An exciting game with amazing graphics",
  "game_type_name": 1,
  "game_icon": {
    "uploadfilename": "file_685f794d79d0e77a1e25d5a2_icon.png",
    "original_filename": "game_icon.png",
    "uploadurl": "public/uploads/file_685f794d79d0e77a1e25d5a2_icon.png",
    "filesize_kb": 45.2
  },
  "game_banner": [
    {
      "uploadfilename": "file_685f794d79d0e77a1e25d5a2_banner1.jpg",
      "original_filename": "banner1.jpg",
      "uploadurl": "public/uploads/file_685f794d79d0e77a1e25d5a2_banner1.jpg",
      "filesize_kb": 120.5
    }
  ],
  "game_assets": {
    "uploadfilename": "file_685f794d79d0e77a1e25d5a2_018f5646.zip",
    "original_filename": "game_assets.zip",
    "uploadurl": "public/temp_uploads/file_685f794d79d0e77a1e25d5a2_018f5646.zip",
    "filesize_kb": 16.86,
    "game_directory": "public/games/my_awesome_game",
    "game_directory_name": "my_awesome_game",
    "extracted_files": ["index.html", "assets/style.css", "assets/script.js", "images/logo.png"],
    "extracted_files_count": 4,
    "extracted_size_kb": 45.2,
    "game_url": "public/games/my_awesome_game"
  },
  "status": 1
}
```

## Features

### Game Type Classification
- **game_type_name**: Required field to classify the game type
  - `1` = FREE (Free games)
  - `2` = COLORSORTINTUBE (Color sorting tube games)

### Automatic Processing
- **Zip Validation**: Ensures the uploaded file is a valid zip archive
- **Directory Creation**: Creates a unique game directory under `public/games/`
- **File Extraction**: Extracts all files from the zip to the game directory
- **Cleanup**: Removes existing game directory before extraction
- **Error Handling**: Provides detailed error messages for failed operations

### Directory Structure
```
public/
├── games/
│   ├── my_awesome_game/
│   │   ├── index.html
│   │   ├── assets/
│   │   │   ├── style.css
│   │   │   └── script.js
│   │   └── images/
│   │       └── logo.png
│   └── another_game/
│       └── ...
├── temp_uploads/
└── uploads/
```

### File Information
All file objects in responses include:
- **uploadfilename**: The generated filename used for storage
- **original_filename**: The original filename as uploaded by the user
- **uploadurl**: The file path for access
- **filesize_kb**: File size in kilobytes

### Response Information
The `game_assets` field in responses includes:
- **game_directory**: Full path to the extracted game directory
- **game_directory_name**: Name of the game directory
- **extracted_files**: List of all extracted files
- **extracted_files_count**: Number of files extracted
- **extracted_size_kb**: Total size of extracted files
- **game_url**: URL path to access the game

## Notes
- The `game_assets` field is **optional** - games can be created without assets
- Only zip files are supported for game assets
- Game directory names are automatically generated from the game name (lowercase, spaces replaced with underscores)
- Existing game directories are replaced when updating assets 