function createNoise(grid) {
  let gradientOnGrid = []
  for (let i = 0; i < grid + 1; i++) {
    gradientOnGrid.push(Math.random() * 2 - 1)
  }
  function smooth(edge0, edge1, t) {
    let i = (6 * Math.pow(t, 5) - 15 * Math.pow(t, 4) + 10 * Math.pow(t, 3))
    return i * (edge1 - edge0) + edge0
  }
  function noise(x) {
    let x_ = x * grid;
    let gridBefore = Math.floor(x_);
    let gridAfter = Math.ceil(x_);
    let gradientBefore = gradientOnGrid[gridBefore];
    let gradientAfter = gradientOnGrid[gridAfter];
    let x_before = x_ - gridBefore;
    let x_after = x_ - gridAfter;
    let rand = smooth(
      gradientBefore * x_before,
      gradientAfter * x_after,
      x_before
    );
    return rand + 0.5
  }
  return noise;
}

function createNormallyDistributedRand(mean, sd) {
  function BoxMuller() {
    const uRand = () => 2 * Math.random() - 1;
    let r1 = uRand();
    let r2 = uRand();
    r_square = -2 * Math.log(r1);
    theta = 2 * Math.PI * r2;
    return Math.pow(r_square, 0.5) * Math.cos(theta);
  }
  function rand() {
    return mean + sd * BoxMuller()
  }
  return rand;
}

function createData(n, days, timeOfDay) {
  function clamp(num) {
    return Math.max(num, 0);
  }
  let data = [];
  for (let i = 0; i < n; i++) {
    let sd = (i + 1) / n * (0.5 / 4);
    let mean = 0;
    let ndRand = createNormallyDistributedRand(mean, sd);
    let noise = createNoise(5);
    for (let day = 0; day < days; day++) {
      for (let timeIndex = 0; timeIndex < timeOfDay; timeIndex++) {
        let time = timeIndex * (3600 * 24 / timeOfDay) + day * 3600 * 24;
        let nTime = timeIndex / timeOfDay;
        const createMockData = (d) => {
          return clamp((noise(nTime) + ndRand()) * d);
        }
        data.push({
          time,
          vendor: "test-" + i,
          location: "sd-" + sd.toFixed(3),
          latency: createMockData(300),
          bandwidth: createMockData(50 * 1024 * 1024),
          packetLoss: Math.min(1, createMockData(0.5))
        })
      }
    }
  }
  let dataAsDict = {}
  for (let d of data) {
    let timeAsString = +d.time;
    if (timeAsString in dataAsDict) {
      dataAsDict[timeAsString].result.push(d)
    } else {
      dataAsDict[timeAsString] = { time: d.time, result: [d] }
    }
  }
  return Object.values(dataAsDict);
}

var data = createData(15, 10, 48);
