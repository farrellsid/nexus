/**
 * Scene recipes: deterministic camera paths the scene director plays and can turn into projects.
 * Nexus ships one, the guided oil tour, which is generated from the sourced stops.
 */

import { oilTourRecipe } from '../nexus/oilTour.ts';

/** Build the recipe list without mutating stored user-authored projects. */
export function createSceneRecipes({ extra = [] } = {}) {
  return [...extra, oilTourRecipe()];
}

export const SCENE_RECIPES = createSceneRecipes();

/** Recipes that append shots to an existing project. None ship yet. */
export const SCENE_APPEND_RECIPES = [];

export function getSceneRecipeById(id) {
  return SCENE_RECIPES.find((recipe) => recipe.id === id) || null;
}

export function getSceneAppendRecipeById(id) {
  return SCENE_APPEND_RECIPES.find((recipe) => recipe.id === id) || null;
}
