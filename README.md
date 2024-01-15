# download paper

This is a Python functionality that download paper from fdu db.

## Installation

You can install the required dependencies using pip:

```
pip install -r requirements
```
## Usage
To use this functionality, run the following command:
```
python download_thesis.py -p {paper_url} -s {local_save_path}
```
## Example
Here's an example of how to use this functionality:
```
python download_thesis.py -p "https://thesis.fudan.edu.cn/onlinePDF?dbid=72&objid=48_50_56_57_49_51&flag=online" -s "D:/毕业论文"
```
### Notes
How to get paper url?
- step 1 : Connect to campus network using VPN
- step 2 : Login "https://thesis.fudan.edu.cn/" and search paper
- step 3: Right-click to view full text and copy link
