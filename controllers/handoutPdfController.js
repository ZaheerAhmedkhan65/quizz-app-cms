import { spawn, spawnSync } from "child_process";
import path from "path";
import fs from "fs";
import db from "../config/db.js";

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



const createLectures = async (req, res) => {
  try {
    const lectures = req.body;
    const COURSE_ID = parseInt(req.params.courseId, 10);

    // Validate input
    if (!lectures || typeof lectures !== "object" || Object.keys(lectures).length === 0) {
      return res.status(400).json({
        success: false,
        message: "Invalid or empty lectures data.",
      });
    }

    // Fetch all existing lectures for this course
    const [existingLectures] = await db.execute(
      `SELECT title FROM lectures WHERE course_id = ?`,
      [COURSE_ID]
    );

    const existingTitles = existingLectures.map((lec) => lec.title.trim().toLowerCase());

    // Prepare new values — skip duplicates (same title for same course)
    const newLectures = Object.entries(lectures).filter(([title, data]) => {
      if (!data || typeof data.start_page !== "number" || typeof data.end_page !== "number") return false;

      // If lecture has a course_id and it mismatches the one in params → skip
      if (data.course_id && parseInt(data.course_id, 10) !== COURSE_ID) return false;

      // Skip if the same title already exists for this course
      return !existingTitles.includes(title.trim().toLowerCase());
    });

    if (newLectures.length === 0) {
      return res.status(200).json({
        success: false,
        message: "No new lectures to add. All titles already exist for this course.",
      });
    }

    // Prepare SQL for bulk insert
    const values = newLectures.map(([title, { start_page, end_page }]) => {
      return `(${COURSE_ID}, ${db.escape(title)}, 0, ${start_page}, ${end_page})`;
    });

    // const sql = `
    //   INSERT INTO lectures (course_id, title, total_questions, start_page, end_page)
    //   VALUES ${values.join(",\n")};
    // `;

    // await db.execute(sql);

    res.json({
      success: true,
      message: "Lectures created successfully.",
      inserted_count: newLectures.length,
      skipped_count: Object.keys(lectures).length - newLectures.length,
    });
  } catch (err) {
    console.error("❌ Error creating lectures:", err);
    res.status(500).json({
      success: false,
      message: "Server error while creating lectures.",
    });
  }
};



export { getHandoutLecures, editPDF, createLectures };