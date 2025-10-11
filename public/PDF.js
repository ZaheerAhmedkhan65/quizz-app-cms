// // when rendering a page:
// const viewport = page.getViewport({ scale: scale });
// // store viewport.width/height & transform

// // convert mouse coords to PDF coords:
// function mouseToPdfCoords(mouseX, mouseY, canvas, viewport) {
//   // canvas bounding rect
//   const rect = canvas.getBoundingClientRect();
//   const x = mouseX - rect.left;
//   const y = mouseY - rect.top;
//   const pdfX = x / viewport.scale;
//   // PDF origin typically bottom-left - depends on PDF.js version / transform
//   const pdfY = (canvas.height - y) / viewport.scale;
//   return { pdfX, pdfY };
// }
