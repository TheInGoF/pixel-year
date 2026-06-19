// Shared frame renderer for the Pixel Year demo loop.
// drawPixelYearFrame(ctx, W, H, t) — t in [0,1), draws one frame at 640x360-ish coords.
(function (root) {
  var MOODS = ['#e26d5c', '#e8a14d', '#e7c84b', '#7bb274', '#57b0a3', '#5b8fd0', '#7b78c9'];
  var BG = '#f6f4ef';
  var EMPTY = '#e7e3db';
  var INK = '#2b2a28';
  var MUTE = '#9a958c';
  var MOON = '#e7c84b';
  var DAYS_IN = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  var MLAB = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  function ease(x) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    return (1 - Math.cos(Math.PI * x)) / 2;
  }
  function smooth(x) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    return x * x * (3 - 2 * x);
  }
  function moodFor(c, r) {
    var h = (Math.imul(c + 1, 73856093) ^ Math.imul(r + 1, 19349663)) >>> 0;
    return MOODS[h % MOODS.length];
  }
  var GRAPHITE = ['#2b2f36', '#3b414a', '#23262b', '#454b54', '#30343b'];
  function graphiteFor(c, r) {
    var h = (Math.imul(c + 1, 73856093) ^ Math.imul(r + 1, 19349663)) >>> 0;
    return GRAPHITE[h % GRAPHITE.length];
  }
  // gaps: ~20% of days left blank, pattern differs per cycle
  function cellOn(c, r, cycle) {
    var h = (Math.imul(c + 3, 2654435761) ^ Math.imul(r + 7, 40503) ^ Math.imul(cycle + 1, 668265263)) >>> 0;
    return (h % 100) >= 20;
  }
  var LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  function letterFor(c, r) {
    var h = (Math.imul(c + 5, 374761393) ^ Math.imul(r + 11, 2246822519)) >>> 0;
    return LETTERS[h % 26];
  }
  function rr(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  // Calendar icon — exact replica of the site favicon (64x64 viewBox).
  function drawCalIcon(ctx, x, y, S) {
    var k = S / 64;
    function R(px, py, w, h, r) { rr(ctx, x + px * k, y + py * k, w * k, h * k, r * k); }
    // binding tabs
    ctx.fillStyle = '#2b2f36';
    R(17, 6, 6, 12, 3); ctx.fill();
    R(41, 6, 6, 12, 3); ctx.fill();
    // page
    ctx.fillStyle = '#ffffff';
    R(6, 12, 52, 46, 7); ctx.fill();
    // red header, clipped to page
    ctx.save();
    R(6, 12, 52, 46, 7); ctx.clip();
    ctx.fillStyle = '#c30000';
    ctx.fillRect(x + 6 * k, y + 12 * k, 52 * k, 13 * k);
    ctx.restore();
    // pixel cells (3x2)
    var cells = [[14, 32, '#3d8bd4'], [27, 32, '#ffd23f'], [40, 32, '#2ea44f'],
                 [14, 45, '#ffd23f'], [27, 45, '#c30000'], [40, 45, '#3d8bd4']];
    for (var i = 0; i < cells.length; i++) { ctx.fillStyle = cells[i][2]; R(cells[i][0], cells[i][1], 9, 9, 2); ctx.fill(); }
    // outline
    ctx.lineWidth = 3 * k; ctx.strokeStyle = '#2b2f36';
    R(6, 12, 52, 46, 7); ctx.stroke();
  }

  // Pencil pointing at its tip (origin), body up-right.
  // Eraser pointing at its tip (origin), body up-right.
  function drawEraser(ctx, tipX, tipY, len, alpha) {
    var w = len * 0.5;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(tipX, tipY);
    ctx.rotate(0.5);
    // pink rubber (lower)
    ctx.fillStyle = '#f1a3ad';
    rr(ctx, -w / 2, -len * 0.64, w, len * 0.64, w * 0.16); ctx.fill();
    // sleeve band (upper)
    ctx.fillStyle = '#5b8fd0';
    rr(ctx, -w / 2, -len, w, len * 0.44, w * 0.16); ctx.fill();
    // outline for definition
    ctx.lineWidth = Math.max(1, len * 0.025);
    ctx.strokeStyle = '#2b2f36';
    rr(ctx, -w / 2, -len, w, len, w * 0.16); ctx.stroke();
    ctx.restore();
  }

  function drawPencil(ctx, tipX, tipY, len, alpha) {
    var w = len * 0.165;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(tipX, tipY);
    ctx.rotate(0.52);
    // graphite tip
    ctx.fillStyle = INK;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-w * 0.5, -len * 0.15);
    ctx.lineTo(w * 0.5, -len * 0.15);
    ctx.closePath(); ctx.fill();
    // wood collar
    ctx.fillStyle = '#d9a86a';
    ctx.fillRect(-w * 0.5, -len * 0.27, w, len * 0.12);
    // body (classic yellow)
    ctx.fillStyle = '#e7c84b';
    rr(ctx, -w * 0.5, -len * 0.92, w, len * 0.65, w * 0.18); ctx.fill();
    // ferrule
    ctx.fillStyle = '#b9b4aa';
    ctx.fillRect(-w * 0.5, -len * 0.99, w, len * 0.09);
    // eraser
    ctx.fillStyle = '#e89aa0';
    rr(ctx, -w * 0.5, -len * 1.06, w, len * 0.09, w * 0.3); ctx.fill();
    ctx.restore();
  }

  function drawPixelYearFrame(ctx, W, H, t) {
    t = ((t % 1) + 1) % 1;

    // ---- background
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, W, H);

    // ---- layout
    var padL = Math.round(W * 0.075);
    var padR = Math.round(W * 0.045);
    var padTop = Math.round(H * 0.30);
    var padBot = Math.round(H * 0.115);
    var cols = 31, rows = 12;
    var gap = Math.max(2, Math.round(W * 0.0045));
    var gridW = W - padL - padR;
    var gridH = H - padTop - padBot;
    var cell = Math.floor(Math.min((gridW - (cols - 1) * gap) / cols, (gridH - (rows - 1) * gap) / rows));
    var stepX = cell + gap, stepY = cell + gap;
    var gridX = padL;
    var gridY = padTop + Math.round((gridH - (rows * stepY - gap)) / 2);

    // ---- three cycles per loop: 0 = colour, 1 = graphite, 2 = letters
    var cycle = Math.min(2, Math.floor(t * 3));
    var lt = (t * 3) - cycle;  // local progress within the cycle

    // ---- animation progress (fill -> hold -> clear, seamless)
    var fillEnd = 0.52, holdEnd = 0.82;
    var p;
    if (lt < fillEnd) p = ease(lt / fillEnd);
    else if (lt < holdEnd) p = 1;
    else p = 1 - ease((lt - holdEnd) / (1 - holdEnd));

    var band = 0.06;

    // ---- grid cells
    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        if (c >= DAYS_IN[r]) continue;
        var x = gridX + c * stepX;
        var y = gridY + r * stepY;
        // empty base
        ctx.fillStyle = EMPTY;
        ctx.fillRect(x, y, cell, cell);
        if (!cellOn(c, r, cycle)) continue; // gap — stays blank
        var colFrac = (c + (r / rows) * 0.5) / cols;
        var reveal = smooth((p - colFrac) / band);
        if (reveal > 0.001) {
          if (cycle < 2) {
            var s = cell * reveal;
            var off = (cell - s) / 2;
            ctx.fillStyle = cycle === 0 ? moodFor(c, r) : graphiteFor(c, r);
            ctx.fillRect(x + off, y + off, s, s);
          } else {
            ctx.save();
            ctx.globalAlpha = reveal;
            ctx.fillStyle = '#2b2f36';
            ctx.font = '700 ' + Math.round(cell * 0.84) + 'px Arial, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(letterFor(c, r), x + cell / 2, y + cell / 2 + 1);
            ctx.restore();
          }
        }
      }
    }

    // ---- month labels
    ctx.fillStyle = MUTE;
    ctx.font = '700 ' + Math.round(cell * 0.62) + 'px Arial, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (var m = 0; m < rows; m++) {
      ctx.fillText(MLAB[m], gridX - gap - 3, gridY + m * stepY + cell / 2 + 1);
    }

    // ---- title + calendar icon
    var titleSize = Math.round(H * 0.092);
    var ty = Math.round(padTop * 0.52);
    var iconS = titleSize * 1.12;
    var iconY = ty - titleSize * 0.34 - iconS / 2;
    drawCalIcon(ctx, padL, iconY, iconS);

    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = INK;
    ctx.font = '800 ' + titleSize + 'px Arial, sans-serif';
    ctx.fillText('Pixel Year', padL + iconS + Math.round(W * 0.022), ty);

    // ---- subtitle
    ctx.fillStyle = MUTE;
    ctx.font = '600 ' + Math.round(H * 0.043) + 'px Arial, sans-serif';
    ctx.fillText('Track your whole year — one pixel a day', padL, ty + Math.round(H * 0.072));

    // ---- footer
    ctx.fillStyle = MUTE;
    ctx.font = '600 ' + Math.round(H * 0.036) + 'px Arial, sans-serif';
    ctx.fillText('Mood + habit tracker  ·  SVG + PDF print', padL, H - Math.round(padBot * 0.38));

    // ---- pencil (filling) / eraser (clearing) riding the front
    if (lt < fillEnd) {
      var penAlpha = Math.min(1, lt / 0.06) * Math.min(1, (fillEnd - lt) / 0.05);
      if (penAlpha > 0.001) {
        var frontCol = Math.max(0, Math.min(cols - 1, Math.round(p * cols)));
        drawPencil(ctx, gridX + frontCol * stepX + cell * 0.5, gridY + cell * 0.45, cell * 5.2, penAlpha);
      }
    } else if (lt > holdEnd) {
      var eraAlpha = Math.min(1, (lt - holdEnd) / 0.05) * Math.min(1, (1 - lt) / 0.05);
      if (eraAlpha > 0.001) {
        var fc = Math.max(0, Math.min(cols - 1, Math.round(p * cols)));
        drawEraser(ctx, gridX + fc * stepX + cell * 0.5, gridY + cell * 0.45, cell * 4.3, eraAlpha);
      }
    }
  }

  root.drawPixelYearFrame = drawPixelYearFrame;
  if (typeof module !== 'undefined' && module.exports) module.exports = { drawPixelYearFrame: drawPixelYearFrame };
})(typeof window !== 'undefined' ? window : globalThis);
