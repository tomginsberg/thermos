# Thermos

![](https://i.imgur.com/txIqpix.jpg)

### Setup

```bash
pip install plotly dash pandas smbus numpy flask
```

### Running the Server

```bash
# start the backend
nohup python backend.py > backend.log &

# start the front end
nohup python liveplot.py > frontend.log &
```