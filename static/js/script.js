console.log("Dashboard Loaded");
document.getElementById("compareBtn").addEventListener("click", function () {
    const file1 = document.getElementById("file1").files[0];
    const file2 = document.getElementById("file2").files[0];

    if (!file1 || !file2) {
        alert("Harap pilih kedua file!");
        return;
    }

    document.getElementById("result").innerHTML =
        "<p>Processing compare... (backend nanti)</p>";
});
// nanti bisa tambah:
// - alert popup
// - loading animation
// - konfirmasi upload