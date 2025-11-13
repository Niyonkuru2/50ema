export const marketSignalEmailTemplate = (
  symbol,
  signal,
  direction,
  timeframe,
  lastClose,
  timestamp
) => `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Market Signal Alert</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', Arial, sans-serif;
      background-color: #f4f4f7;
      color: #111827;
    }
    .container {
      max-width: 600px;
      margin: 40px auto;
      background: #ffffff;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .header {
      background-color: #1a73e8;
      color: #ffffff;
      text-align: center;
      padding: 20px;
      font-size: 24px;
      font-weight: bold;
    }
    .content {
      padding: 30px;
      font-size: 16px;
      line-height: 1.6;
    }
    .signal {
      display: inline-block;
      padding: 10px 20px;
      border-radius: 8px;
      color: #ffffff;
      font-weight: bold;
      text-transform: uppercase;
    }
    .buy { background-color: #28a745; }
    .sell { background-color: #dc3545; }
    .neutral { background-color: #6c757d; }
    .direction {
      display: inline-block;
      padding: 5px 12px;
      border-radius: 6px;
      font-weight: bold;
      text-transform: uppercase;
      color: #fff;
    }
    .up { background-color: #16a34a; }
    .down { background-color: #dc2626; }
    .neutral-dir { background-color: #6b7280; }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    .data-table th, .data-table td {
      text-align: left;
      padding: 10px;
      border-bottom: 1px solid #e5e7eb;
    }
    .data-table th {
      background-color: #f9fafb;
      font-weight: bold;
    }
    .footer {
      text-align: center;
      font-size: 13px;
      color: #6b7280;
      padding: 20px;
      background-color: #f9fafb;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">Market Signal Alert</div>
    <div class="content">
      <p>Hello Trader,</p>
      <p>Our algorithm has detected a new market signal:</p>

      <p><strong>Symbol:</strong> ${symbol}</p>
      <p><strong>Timeframe:</strong> ${timeframe}</p>

      <p><strong>Signal:</strong> 
        <span class="signal ${signal === "BUY" ? "buy" : signal === "SELL" ? "sell" : "neutral"}">
          ${signal}
        </span>
      </p>

      <p><strong>Direction:</strong>
        <span class="direction ${direction === "UP" ? "up" : direction === "DOWN" ? "down" : "neutral-dir"}">
          ${direction}
        </span>
      </p>

      <table class="data-table">
        <tr><th>Last Close</th><td>${lastClose ?? "—"}</td></tr>
  
        <tr><th>Timestamp</th><td>${timestamp ?? new Date().toISOString()}</td></tr>
      </table>

      <p>Check your chart to confirm and manage the trade carefully.</p>
    </div>
    <div class="footer">
      &copy; ${new Date().getFullYear()} Market Signal System. All rights reserved.
    </div>
  </div>
</body>
</html>
`;
