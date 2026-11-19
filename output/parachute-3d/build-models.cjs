const fs = require('fs');
const vm = require('vm');
const path = require('path');
const source = path.join(__dirname, '..', 'parachute-python', 'shape.html');
const html = fs.readFileSync(source, 'utf8');
const js = html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(js); // Parse the complete interactive program.
const geom = js.split('// GEOMETRY_START')[1].split('// GEOMETRY_END')[0];
const context = vm.createContext({Math});
vm.runInContext(geom, context);
for (const mode of ['compare', 'main', 'drogue']) {
  const model = vm.runInContext(`createGeometry('${mode}', 1)`, context);
  let idx = 1;
  const rows = ['# Circular parachute concept model', '# Units: meters; +Y up', '# Nominal flat diameters derived from areas 6.05 and 2.12 m^2', '# Deployed spherical-cap illustration, not FSI/CAD cutting pattern', '# OBJ lines represent suspension lines, not solid cylinders'];
  for (const group of [...new Set(model.faces.map(f => f.group))]) {
    rows.push('o ' + group);
    for (const f of model.faces.filter(f => f.group === group)) {
      for (const p of f.points) {
        if (!p.every(Number.isFinite)) throw new Error('Nonfinite mesh vertex');
        rows.push('v ' + p.map(x => x.toFixed(6)).join(' '));
      }
      rows.push(`f ${idx} ${idx+1} ${idx+2}`);idx += 3;
    }
  }
  for (const group of [...new Set(model.lines.map(l => l.group))]) {
    rows.push('o ' + group);
    for (const l of model.lines.filter(l => l.group === group)) {
      rows.push('v ' + l.a.map(x => x.toFixed(6)).join(' '));
      rows.push('v ' + l.b.map(x => x.toFixed(6)).join(' '));
      rows.push(`l ${idx} ${idx+1}`);idx += 2;
      if (group.endsWith('_lines')) {
        const length = Math.hypot(...l.a.map((x,i)=>x-l.b[i]));
        const target = group.startsWith('main') ? 3.45 : 2.05;
        if (Math.abs(length-target)>1e-9) throw new Error('Suspension length mismatch');
      }
    }
  }
  fs.writeFileSync(path.join(__dirname, 'parachute-'+mode+'.obj'),rows.join('\n')+'\n');
  console.log(mode, model.faces.length+' triangles',model.lines.length+' edges; geometry checks OK');
}
