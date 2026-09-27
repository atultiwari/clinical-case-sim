-- Nidana: players can change their nickname and training level and withdraw research consent
-- (Nidana PLAN N1.6; SPEC §12). Proposed by a Nidana session; a Case Library session applies it.
--
-- nidana_server could insert play.player rows but not change them. This grants update on the
-- three profile columns only; id and created_at (the moment the player agreed) stay fixed.

grant update (display_name, training_level, consent_research) on play.player to nidana_server;
