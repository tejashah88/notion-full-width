# notion-full-width
A simple Python CLI tool to set the "Full width" option for all pages across a Notion workspace.

## Features
* Set the full width setting for **all** pages within a workspace (that you own).
* Login **directly** from the CLI tool.
* Prompts you to select the workspace if it encounters multiple workspaces.
* Gracefully **skips** over pages which the user doesn't have edit access.

## README before running the script
* If you used a 3rd-party provider like Google to login, you'll need to set an explicit password.
    * Go to "Settings & Members" > "My Account" > "Password" > "Set a password"
* If you try to run this tool too many times, you'll get a 429 Rate Limited error from trying to login too many times. You will be locked out from logging back in for **at least 1 hour**.

## Usage

### Setup
Clone this repository and install the required dependencies ([notion-py](https://github.com/jamalex/notion-py) and [tqdm](https://github.com/tqdm/tqdm)).

### Syntax
```bash
python cli.py <email> [setting] [delay]
```

* `email` - The email associated with your Notion account.
* `setting` - The boolean value to set the "Full Width" setting for the pages.
* `delay` - The amount of time (in seconds) to set the "Full Width" setting between pages.

### Examples
```bash
python cli.py example@gmail.com
python cli.py example@gmail.com true
python cli.py example@gmail.com false 0.5
```
