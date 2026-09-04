import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Layer,
  Rectangle,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_URL = "";
const PAGE_SIZE = 10;

function OverlapBar({ x, y, width, height, payload }) {
  const lava = payload.lava;
  const random = payload.random;

  const maxValue = Math.max(lava, random, 1);

  const lavaHeight = height * (lava / maxValue);
  const randomHeight = height * (random / maxValue);

  return (
    <g>
      <rect
        x={x}
        y={y + height - lavaHeight}
        width={width}
        height={lavaHeight}
        fill="#ff6b35"
        fillOpacity={0.6}
      />

      <rect
        x={x}
        y={y + height - randomHeight}
        width={width}
        height={randomHeight}
        fill="#4285f4"
        fillOpacity={0.6}
      />
    </g>
  );
}

function calculateStats(values) {
  if (values.length === 0) {
    return {
      count: 0,
      minimum: null,
      maximum: null,
      mean: null,
      standardDeviation: null,
      chiSquare: null,
    };
  }

  const count = values.length;
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);

  const mean =
    values.reduce((sum, value) => sum + value, 0) / count;

  const variance =
    values.reduce(
      (sum, value) => sum + (value - mean) ** 2,
      0
    ) / count;

  const standardDeviation = Math.sqrt(variance);

  const bucketCount = 100;
  const bucketSize = 4294967296 / bucketCount;
  const expected = count / bucketCount;

  const buckets = Array(bucketCount).fill(0);

  for (const value of values) {
    const index = Math.min(
      Math.floor(value / bucketSize),
      bucketCount - 1
    );

    buckets[index]++;
  }

  const chiSquare = buckets.reduce(
    (sum, observed) =>
      sum + ((observed - expected) ** 2) / expected,
    0
  );

  return {
    count,
    minimum,
    maximum,
    mean,
    standardDeviation,
    chiSquare,
  };
}


function App() {
  const [stats, setStats] = useState(null);
  const [samples, setSamples] = useState([]);
  const [distribution, setDistribution] = useState([]);
  const [distributionStats, setDistributionStats] = useState(null);
  const [page, setPage] = useState(0);

  const [selectedImage, setSelectedImage] = useState(null);
  const [rngValue, setRngValue] = useState(null);
  const [rngLoading, setRngLoading] = useState(false);
  const [rngError, setRngError] = useState(null);

  async function loadStats() {
    const response = await fetch(`${API_URL}/api/stats`);

    if (!response.ok) {
      throw new Error("Failed to load statistics");
    }

    setStats(await response.json());
  }

  async function loadSamples(currentPage = page) {
    const response = await fetch(
      `${API_URL}/api/samples?limit=${PAGE_SIZE}&offset=${currentPage * PAGE_SIZE}`
    );

    if (!response.ok) {
      throw new Error("Failed to load samples");
    }

    const data = await response.json();
    setSamples(data.samples);
    return data;
  }

  async function loadDistribution() {
  const response = await fetch(`${API_URL}/api/stats/distribution`);

  if (!response.ok) {
    throw new Error("Failed to load distribution");
  }

  const data = await response.json();


  const lavaStats = calculateStats(data.lava);
  const randomStats = calculateStats(data.random);

  setDistributionStats({
    lava: lavaStats,
    random: randomStats,
  });

  const bucketCount = 100;
  const bucketSize = 4294967296 / bucketCount;
  const bucketPercentage = 100 / bucketCount;

  const buckets = Array.from({ length: bucketCount }, (_, index) => ({
    range: `${index * bucketPercentage}-${(index + 1) * bucketPercentage}%`,
    lava: 0,
    random: 0,
  }));

  for (const value of data.lava) {
    const index = Math.min(
      Math.floor(value / bucketSize),
      bucketCount - 1
    );

    buckets[index].lava++;
  }

  for (const value of data.random) {
    const index = Math.min(
      Math.floor(value / bucketSize),
      bucketCount - 1
    );

    buckets[index].random++;
  }

  setDistribution(buckets);
}

  async function loadData() {
    try {
      await Promise.all([
        loadStats(),
        loadSamples(0),
        loadDistribution(),
      ]);
    } catch (error) {
      console.error(error);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function requestRng() {
    setRngLoading(true);
    setRngError(null);

    try {
      const response = await fetch(
        `${API_URL}/api/rng?client=website`
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "No RNG value available");
      }

      const data = await response.json();

      setRngValue(data);

      // Refresh counters and history because this sample was consumed.
      await Promise.all([
        loadStats(),
        loadSamples(page),
      ]);
    } catch (error) {
      setRngError(error.message);
    } finally {
      setRngLoading(false);
    }
  }

  async function changePage(newPage) {
    setPage(newPage);
    await loadSamples(newPage);
  }

  if (!stats) {
    return (
      <div className="app">
        <h1>Lava RNG</h1>
        <p>Loading...</p>
      </div>
    );
  }

  const totalPages = Math.ceil(stats.total / PAGE_SIZE);

  return (
    <div className="app">
      <header className="header">
        <h1>Lava RNG</h1>
        <p>
          Random numbers generated from physical lava lamp entropy.
        </p>
      </header>

      {/* RNG */}
      <section className="rng-section">
        <div>
          <h2>Get a random number</h2>
          <p>
            Request the next available value from the entropy pool.
          </p>
        </div>

        <button
          className="rng-button"
          onClick={requestRng}
          disabled={rngLoading || stats.available === 0}
        >
          {rngLoading ? "Requesting..." : "Generate RNG"}
        </button>

        {stats.available === 0 && (
          <p className="warning">
            No unused RNG samples are currently available.
          </p>
        )}

        {rngError && (
          <p className="error">
            {rngError}
          </p>
        )}

        {rngValue && (
          <div className="result">
            <span>Random value</span>
            <strong>{rngValue.value}</strong>

            <small>
              Sample #{rngValue.sample_id} ·{" "}
              {new Date(rngValue.timestamp).toLocaleString()}
            </small>
          </div>
        )}
      </section>

      {/* Statistics */}
      <section>
        <h2>Statistics</h2>

        <div className="stats">
          <div className="card">
            <span>Available</span>
            <strong>{stats.available}</strong>
          </div>

          <div className="card">
            <span>Total generated</span>
            <strong>{stats.total}</strong>
          </div>

          <div className="card">
            <span>Consumed</span>
            <strong>{stats.consumed}</strong>
          </div>

          <div className="card">
            <span>Average</span>
            <strong>
              {stats.average === null
                ? "-"
                : Math.round(stats.average)}
            </strong>
          </div>

          <div className="card">
            <span>Minimum</span>
            <strong>{stats.minimum ?? "-"}</strong>
          </div>

          <div className="card">
            <span>Maximum</span>
            <strong>{stats.maximum ?? "-"}</strong>
          </div>
        </div>
      </section>

      {/* Distribution */}
      <section className="chart-section">
        <h2>RNG distribution</h2>

        <p>
          Distribution of generated values across the 32-bit unsigned
          integer range.
        </p>

        <div className="chart">
  <ResponsiveContainer width="100%" height={350}>
  <AreaChart
    data={distribution}
    margin={{ top: 10, right: 20, left: 20, bottom: 40 }}
  >
    <CartesianGrid strokeDasharray="3 3" />

    <XAxis
      dataKey="range"
      label={{
        value: "Position in uint32 range",
        position: "insideBottom",
        offset: -5,
      }}
    />

    <YAxis
      allowDecimals={false}
      label={{
        value: "Samples",
        angle: -90,
        position: "insideLeft",
      }}
    />

    <Tooltip />

    <Legend />

    <Area
      type="step"
      dataKey="lava"
      name="Lava RNG"
      fill="#ff6b35"
      fillOpacity={0.45}
      stroke="#ff6b35"
    />

    <Area
      type="step"
      dataKey="random"
      name="Python random"
      fill="#4285f4"
      fillOpacity={0.45}
      stroke="#4285f4"
    />
  </AreaChart>
</ResponsiveContainer>
</div>
        {distributionStats && (
          <div className="stats">
            <div className="card">
              <span>Samples</span>
              <strong>{distributionStats.lava.count}</strong>
            </div>

            <div className="card">
              <span>Lava mean</span>
              <strong>
                {distributionStats.lava.mean === null
                 ? "-"
                 :Math.round(distributionStats.lava.mean)}
              </strong>
            </div>

            <div className="card">
              <span>Python random mean</span>
              <strong>
                {distributionStats.random.mean === null
                 ? "-"
                 : Math.round(distributionStats.random.mean)}
              </strong>
            </div>

            <div className="card">
              <span>Lava std. deviation</span>
              <strong>
                {distributionStats.lava.standardDeviation === null
                 ? "-"
                 : Math.round(distributionStats.lava.standardDeviation)}
              </strong>
            </div>

            <div className="card">
              <span>Python random std. deviation</span>
              <strong>
                {distributionStats.random.standardDeviation === null
                 ? "-"
                 : Math.round(distributionStats.random.standardDeviation)}
              </strong>
            </div>

           <div className="card">
             <span>Lava χ²</span>
              <strong>
                {distributionStats.lava.chiSquare === null
                 ? "-"
                 : distributionStats.lava.chiSquare.toFixed(2)}
              </strong>
           </div>

           <div className="card">
            <span>Python random χ²</span>
             <strong>
               {distributionStats.random.chiSquare === null
                ? "-"
                : distributionStats.random.chiSquare.toFixed(2)}
             </strong>
          </div>
          
         </div>
        )}


      </section>

      {/* Sample history */}
      <section>
        <h2>Sample history</h2>

        {samples.length === 0 ? (
          <p>No samples available.</p>
        ) : (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Image</th>
                    <th>RNG value</th>
                    <th>Timestamp</th>
                    <th>Algorithm</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {samples.map((sample) => (
                    <tr key={sample.id}>
                      <td>{sample.id}</td>
                       <td>
                        <img
                         src={`${API_URL}/${sample.image_path}`}
                         alt={`Sample ${sample.id}`}
                         className="sample-image"
                         onClick={() => setSelectedImage(sample)}
                        />
                       </td>
                      
                      <td className="number">
                        {sample.rng_value}
                      </td>

                      <td>
                        {new Date(
                          sample.timestamp
                        ).toLocaleString()}
                      </td>

                      <td>
                        {sample.algorithm}{" "}
                        {sample.algorithm_version}
                      </td>

                      <td>
                        <span
                          className={
                            sample.used
                              ? "status used"
                              : "status available"
                          }
                        >
                          {sample.used
                            ? "Consumed"
                            : "Available"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <button
                onClick={() => changePage(page - 1)}
                disabled={page === 0}
              >
                Previous
              </button>

              <span>
                Page {page + 1} of {Math.max(totalPages, 1)}
              </span>

              <button
                onClick={() => changePage(page + 1)}
                disabled={page + 1 >= totalPages}
              >
                Next
              </button>
            </div>
          </>
        )}
      </section>
{selectedImage && (
  <div
    className="image-modal"
    onClick={() => setSelectedImage(null)}
  >
    <div
      className="image-modal-content"
      onClick={(event) => event.stopPropagation()}
    >
      <button
        className="image-modal-close"
        onClick={() => setSelectedImage(null)}
        aria-label="Close image preview"
      >
        ×
      </button>

      <img
        src={`${API_URL}/${selectedImage.image_path}`}
        alt={`Sample ${selectedImage.id}`}
        className="image-modal-image"
      />

      <p>Sample #{selectedImage.id}</p>
    </div>
  </div>
)}
     </div>
  );
}

export default App;
