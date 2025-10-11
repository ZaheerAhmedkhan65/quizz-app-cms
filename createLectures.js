import db from "./config/db.js";
import lectures from "./lectures.json" assert { type: "json" };
const COURSE_ID = 690018; // change this to the course_id you want

(async () => {
  try {                                                                                                                                                                                     
    const values = Object.entries(lectures).map(([title, { start_page, end_page }]) => {
      return `(${COURSE_ID}, ${db.escape(title)}, 0, ${start_page}, ${end_page})`;
    });

    const sql = `
      INSERT INTO lectures (course_id, title, total_questions, start_page, end_page)
      VALUES ${values.join(",\n")};
    `;

    console.log(sql); // preview query
    await db.execute(sql);
    console.log("✅ Bulk create complete");
  } catch (err) {
    console.error("❌ Error:", err);
  } finally {
    process.exit();
  }
})();