let particles = [];

function setup() {
  let canvas = createCanvas(400, 400);
  canvas.parent('canvas-container');
  for (let i = 0; i < 5; i++) {
    particles.push(new Particle(random(width), random(height)));
  }
}

function draw() {
  background(0);
  for (let particle of particles) {
    particle.update();
    particle.show();
  }
}

class Particle {
  constructor(x, y) {
    this.pos = createVector(x, y);
    this.vel = p5.Vector.random2D();
    this.acc = createVector(0, 0);
  }

  update() {
    this.vel.add(this.acc);
    this.pos.add(this.vel);
    this.acc.mult(0);
  }

  show() {
    stroke(255);
    strokeWeight(4);
    point(this.pos.x, this.pos.y);
  }
}