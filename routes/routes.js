import express from "express";
import upload from "../middlewares/upload.js";
import { editPDF, getHandoutLecures, createLectures } from "../controllers/handoutPdfController.js";

const router = express.Router();

router.get("/get_lectures", (req, res) => {
    res.render("get_lectures");
});

router.get("/edit_pdf", (req, res) => {
    res.render("edit_pdf");
});

router.post("/get_lectures", upload.single("pdf"), getHandoutLecures);
router.post('/edit/remove', upload.single('pdf'), editPDF);
router.post('/create_lectures/:courseId', createLectures);

router.get('/download/:file', (req, res) => {
  const file = path.join(process.cwd(), 'edited', req.params.file);
  res.download(file);
});

export default router;
