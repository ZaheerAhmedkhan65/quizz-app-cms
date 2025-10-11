import { spawn, spawnSync } from "child_process";
import path from "path";
import fs from "fs";

const getHandoutLecures = (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, error: "No PDF file uploaded" });
    }

    // Set headers for Server-Sent Events
    res.writeHead(200, {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Transfer-Encoding': 'chunked'
    });

    const filePath = path.resolve(req.file.path);
    const python = spawn("python", ["utiles/parse_pdf.py", filePath]);

    let finalData = "";
    let jsonData = null;

    python.stderr.on("data", (chunk) => {
      const chunkStr = chunk.toString();

      // Check for progress updates
      const progressMatch = chunkStr.match(/PROGRESS:(\d+)/);
      if (progressMatch) {
        const progress = progressMatch[1];
        // Send progress update to client
        res.write(`data: ${JSON.stringify({ type: "progress", progress: parseInt(progress) })}\n\n`);
      } else if (chunkStr.trim()) {
        console.error("Python error:", chunkStr);
        res.write(`data: ${JSON.stringify({ type: "error", error: chunkStr })}\n\n`);
      }
    });

    python.stdout.on("data", (chunk) => {
      finalData += chunk.toString();
    });

    python.on("close", (code) => {
      fs.unlinkSync(filePath); // cleanup

      try {
        if (finalData) {
          jsonData = JSON.parse(finalData);
          //   const pages = Object.keys(jsonData).length;

          // Send final result
          res.write(`data: ${JSON.stringify({
            type: "complete",
            success: true,
            lectures: JSON.stringify(jsonData, null, 2)
          })}\n\n`);
        } else {
          res.write(`data: ${JSON.stringify({
            type: "complete",
            success: false,
            error: "No data received from Python script"
          })}\n\n`);
        }
      } catch (err) {
        res.write(`data: ${JSON.stringify({
          type: "complete",
          success: false,
          error: "Failed to parse Python output: " + err.message
        })}\n\n`);
      } finally {
        res.end();
      }
    });

    python.on("error", (error) => {
      res.write(`data: ${JSON.stringify({
        type: "complete",
        success: false,
        error: "Python script error: " + error.message
      })}\n\n`);
      res.end();
    });

  } catch (error) {
    res.write(`data: ${JSON.stringify({
      type: "complete",
      success: false,
      error: error.message
    })}\n\n`);
    res.end();
  }
};

const editPDF = (req, res) => {
  try {
    const { actions, outFile } = req.body;
    const filePath = path.resolve(req.file.path);
    console.log(filePath, actions, outFile);
    const python = spawn('python3', ['pdf_edit.py', JSON.stringify({ filePath, actions, outFile })]);

    let stdout = '', stderr = '';
    python.stdout.on('data', d => stdout += d.toString());
    python.stderr.on('data', d => stderr += d.toString());
    python.on('close', code => {
      if (code === 0) {
        res.json({ success: true, outFile });
      } else {
        res.status(500).json({ success: false, error: stderr || stdout });
      }
    });
  } catch (error) {
    console.error(error);
  }
};

export { getHandoutLecures, editPDF };