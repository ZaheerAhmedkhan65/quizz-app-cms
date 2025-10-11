import express from "express";
import cors from "cors";
import routes from "./routes/routes.js";
const app = express();


app.use(express.urlencoded({ extended: true }));
app.use(cors());
app.use(express.json());
app.use(express.static('public'));
app.set("view engine", "ejs");

// Routes
app.get("/", (req, res) => {
    res.render("index");
});

app.use(routes);

app.get("/editor", (req, res) => {
    res.render("editor");
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Server error:', err);
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

app.use((req, res) => {
    res.status(404).render('404');
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
    console.log(`PDF Editor running at http://localhost:${PORT}`);
});